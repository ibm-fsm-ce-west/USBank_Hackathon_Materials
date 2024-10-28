import warnings

warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from flask import Flask, request
from ibm_watsonx_ai.client import APIClient as wxAPIClient
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson_openscale import APIClient as WOSAPIClient
from ibm_watson_openscale.data_sets import DataSetTypes, TargetTypes
from ibm_watson_openscale.supporting_classes.enums import *
from ibm_watson_openscale.supporting_classes.payload_record import PayloadRecord
from langchain.embeddings import SentenceTransformerEmbeddings
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from PyPDF2 import PdfReader
import os
import requests
import pandas as pd


## Load environment variables .env
load_dotenv(override=True)

"""
get_OpenScale_creds()
Inputs: none
Outputs: none
Description: uses the api key and subscription id to set up the Watson OpenScale client and retreive the paylod logging dataset
Purpose: enables .gov metric scoring
Returns: Watson OpenScale client and payload logging data set id in a tuple
"""
def get_OpenScale_creds():

    authenticator = IAMAuthenticator(
        apikey=os.getenv("APIKEY"), url=os.getenv("IBM_AUTH_URL")
    )

    SUBSCRIPTION_ID = os.getenv("SUBSCRIPTION_ID")
    
    wos_client = WOSAPIClient(
        authenticator=authenticator, service_url=os.getenv("OPENSCALE_URL")
        )
        
    payload_logging_data_set_id = (
        wos_client.data_sets.list(
            type=DataSetTypes.PAYLOAD_LOGGING,
            target_target_id=SUBSCRIPTION_ID,
            target_target_type=TargetTypes.SUBSCRIPTION,
        )
        .result.data_sets[0]
        .metadata.id
    )

    return (wos_client, payload_logging_data_set_id)


"""
push_record()
Inputs: 
    - context (array of 3 context strs)
    - question (str)
    - answer (str)
Outputs: none
Description: pushes payload data to OpenScale datamart
Purpose: manual scoring - ONLY FOR WHEN NOT USING WATSONX.AI DEPLOYMENT!
Returns: True on success
"""
def push_record(context, question, answer):
    print("Pushing record...")
    scoring_request = {
        "fields": ["context1", "context2", "context3", "question"],
        "values": [[context[0], context[1], context[2], question]],
    }
    scoring_response = {"predictions": [{"fields": ["answer"], "values": [[answer]]}]}

    records_list = []
    pl_record = PayloadRecord(request=scoring_request, response=scoring_response)
    records_list.append(pl_record)

    response = wos_client.data_sets.store_records(
        data_set_id=payload_logging_data_set_id,
        request_body=records_list,
        background_mode=True,
    )

    return True


"""
extract_pdf_text(file_path)
Inputs: 
    - file_path: file path of pdf to extract text from (str)
Outputs: none
Description: extracts the text from pdf files
Purpose: for ingestion of pdf documents into watsonx Discovery to perform RAG
Returns: extracted text
"""
def extract_pdf_text(file_path):
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text() or ''
    return text

# Function to generate documents for bulk indexing
"""
generate_documents(folder_path, index_name, emb_func)
Inputs: 
    - folder_path: path of folder with your documents
    - index_name: name of index in watsonx Discovery
    - emb_func: embedding function used to embed these documents
Outputs: exception messages upon errors
Description: generates documents from the knowledge base
Purpose: used to bulk index the knowledge base documents, to then embed them for RAG
Returns: document dictionaries ready for bulk indexing
"""
def generate_documents(folder_path, index_name, emb_func):

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if filename.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            elif filename.endswith('.pdf'):
                content = extract_pdf_text(file_path)
            else:
                # Handle other file types (optional, may need appropriate libraries)
                with open(file_path, 'rb') as file:
                    content = file.read()  # Read binary for unsupported formats
                # Convert to string if necessary, else store as binary in a different way

            # Create 256-character chunks with 128-character overlap
            chunks = [content[i:i + 256] for i in range(0, len(content) - 128, 128)]
            counter = 0  # Counter to ensure unique IDs for each chunk

            for chunk in chunks:
                # Create each document as a dictionary with '_index' for bulk indexing
                yield {
                    "_index": index_name,
                    "_id": f"{filename}-{counter}",
                    "_source": {
                        "embedding": emb_func.embed_documents([chunk])[0],
                        "text": chunk
                    }
                }
                counter += 1

        except Exception as e:
            print(f"Error processing {filename}: {e}")


"""
watsonx_discovery_setup()
Inputs: none
Outputs: updates on index creation, mapping on successful indexing
Description: sets up watsonx Discovery (Elastic Search) for RAG by bulk indexing knowledge base docs into the vector db
Purpose: using RAG in the custom extension
Returns: True on success, False when index with chosen name already exists
"""
def watsonx_discovery_setup():
    
    # connect to watsonx Discovery (Elastic Search)
    eshost = os.getenv("ELASTIC_SEARCH_HOST")
    esport = os.getenv("ELASTIC_SEARCH_PORT")
    esuser = os.getenv("ELASTIC_SEARCH_USERNAME")
    espass = os.getenv("ELASTIC_SEARCH_PASSWORD")

    elastic_client = Elasticsearch([f"{eshost}:{esport}"], basic_auth=(esuser, espass), verify_certs=False, ssl_show_warn=False)
    
    index_name = os.getenv("INDEX_NAME")
    
    # ensure we don't doubly create indices
    if elastic_client.indices.exists(index=index_name):
        print(index_name + " exists") # if you wish to delete the old index and recreate it, modify this section
        return False
    
    emb_func = SentenceTransformerEmbeddings(model_name=os.getenv("EMBEDDING_FUNCTION_MODEL"))
    dims = emb_func.client.get_sentence_embedding_dimension()
    # create Elasticsearch index to index the data
    mapping = {
            "properties": {
                    "text": {
                            "type": "text"
                        },
                    "embedding": {
                            "type": "dense_vector",
                            "dims": dims,
                            "index": True,
                            "similarity": "l2_norm"
                        }
                }
        }
    
    elastic_client.indices.create(index=index_name, mappings=mapping)
    print("Creating " + index_name)

    folder_path = f"{os.getcwd()}/knowledge_base"

    # Bulk index documents
    bulk(elastic_client, generate_documents(folder_path, index_name, emb_func), index=index_name)

    elastic_client.indices.refresh(index=index_name)
    
    mapping = elastic_client.indices.get_mapping(index=index_name)
    print(mapping)

    return True

"""
ask_question()
Inputs:
    - question (str): The question to be answered
Outputs: status codes, the response, and context
Description: Ask a question and get a RAG response
Purpose: to prompt the LLM and get an answer grounded in context
Returns: 
    - data (DataFrame): A DataFrame containing the context, source file names, question, and answer.
"""
def ask_question(
    question: str
):
    # set the embedding function model
    emb_func = SentenceTransformerEmbeddings(model_name=os.getenv("EMBEDDING_FUNCTION_MODEL"))

    # connect to watsonx Discovery (Elastic Search)
    eshost = os.getenv("ELASTIC_SEARCH_HOST")
    esport = os.getenv("ELASTIC_SEARCH_PORT")
    esuser = os.getenv("ELASTIC_SEARCH_USERNAME")
    espass = os.getenv("ELASTIC_SEARCH_PASSWORD")
    elastic_client = Elasticsearch([f"{eshost}:{esport}"], basic_auth=(esuser, espass), verify_certs=False, ssl_show_warn=False)

    # query elastic search to get the relevant context for watsonx.ai
    index_name = os.getenv("INDEX_NAME")
    embedded_question = emb_func.embed_query(question)

    relevant_chunks = elastic_client.search(
        index=index_name,
        knn={
            "field": "embedding",
            "query_vector": embedded_question,
            "k": 4,
            "num_candidates": 50,
            },
        _source=[
                    "text",
                    "filename"
                ],
        size=3
                                
    )

    #print(relevant_chunks)

    hits = relevant_chunks['hits']['hits']

    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": os.getenv("APIKEY")
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    # Get IAM Token for generate answer request
    response = requests.post(os.getenv("IBM_AUTH_URL"), data=data, headers=headers, verify=False)
    print(response.status_code)

    relevant_chunks = [hits[0]["_source"]['text'], hits[1]["_source"]['text'], hits[2]["_source"]['text']]
  
    # Create data payload for generate answer request
    data = {
        "parameters": {
            "prompt_variables": {
                "context1": relevant_chunks[0],
                "context2": relevant_chunks[1],
                "context3": relevant_chunks[2],
                "question": question
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Bearer {}".format(response.json().get("access_token"))
    }

    # Perform the POST request
    response = requests.post(os.getenv("DEPLOYED_PROMPT_TEMPLATE_ENDPOINT"), headers=headers, json=data)

    print(response.status_code)
    print(response.json())
    response = response.json().get("results")[0]["generated_text"]
    # Remove leading and trailing whitespace from the response
    response = response.strip()

    print("Answer:")
    print(response)

    # Print metrics
    data = pd.DataFrame([relevant_chunks], columns=["context1", "context2", "context3"])
    print("Context:")
    print(data)
    

    data["question"] = question
    data["answer"] = response

    # Sends dataset to OpenScale datamart ONLY NEEDED IF you are not using a deployed wx.ai endpoint.
    #push_record(relevant_chunks, question, response)

    return data

####### MAIN START

app = Flask(__name__)

#Helper Client connection to watsonx.ai
credentials = {"url": os.getenv("WATSONXAI_ENDPOINT"), "apikey": os.getenv("APIKEY")}
client = wxAPIClient(credentials)
client.set.default_project(os.getenv("PROJECT_ID"))
watsonx_discovery_setup()

#Helper Client connection to watsonx.governance
#wos_client, payload_logging_data_set_id = get_OpenScale_creds()


"""
generate_results()
Inputs: none
Parameters:
    - request (flask.Request): The incoming request object containing the JSON data.
Outputs: none
Description: calls the ask question function and returns the answer
Purpose: app api endpoint to pass the question and return the result
Returns: flask.Response: A JSON response containing the results of the prediction.
"""
@app.route("/generate_results", methods=["POST"])
def generate_results():
    # Get the input parameters from the request
    data = request.json
    # Call the predict function to generate results
    result = ask_question(data.get("question"))

    # Convert the result DataFrame to JSON format and return the response
    return result.to_json(orient="records")

"""
This is the main executable that sets up the necessary credentials, initializes the embeddings and LLM model,
and then starts a Flask server to handle POST requests for generating results.
"""
if __name__ == "__main__":
    app.run(host=os.getenv("FLASK_RUN_HOST"), port=os.getenv("FLASK_RUN_PORT"))
