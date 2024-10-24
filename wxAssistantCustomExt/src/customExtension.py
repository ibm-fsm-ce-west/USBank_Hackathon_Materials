"""
To execute the code, you will need to have the necessary dependencies installed from requirements.txt.
Additionally, you will need to set up the necessary environment variables as seen in .env-sample.

The code also includes a main executable section that sets up the necessary credentials and starts a Flask server to handle POST requests for 
generating results.

Please note that the code provided is a complex and comprehensive implementation, and it may require further customization and modification 
to fit your specific requirements. It is recommended to review and understand the code thoroughly before using it in a production environment.
"""

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
import os
import requests
import pandas as pd


## Load environment variables .env
load_dotenv()

def getOpenScaleCreds():

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

# Helper function to push payload data to OpenScale datamart. NOT NEEDED IF USING WATSONX.AI DEPLOYMENT FOR GENAI FUNCTIONALITY
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


def ask_question(
    question: str
):
    """
    Ask a question and get a response.

    Parameters:
    collection_name (str): The name of the Milvus collection to create or use.
    question (str): The question to be answered.
    pdf_chunks_dict (dict): A dictionary where the keys are the names of the PDF files and the values are lists of chunks from the PDF files.

    Returns:
    data (DataFrame): A DataFrame containing the context, source file names, question, and answer.
    """

    #HEY GIRISH
    #Here is where we need to add the watsonx Discovery query code
    
    #results = query_milvus(collection_name, question)
    #relevant_chunks = [result.get("entity").get("content") for result in results[0]]
    #relevant_filenames = [result.get("entity").get("source_title") for result in results[0]]


    data = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": os.getenv("APIKEY")  # Replace this with your actual API key
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    # Get IAM Token for generate answer request
    response = requests.post(os.getenv("IBM_AUTH_URL"), data=data, headers=headers, verify=False)
    print(response.status_code)
  
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
    
    dataFiles = pd.DataFrame(
        [relevant_filenames], columns=["fileName1", "fileName2", "fileName3"]
    )
    print("File names:")
    print(dataFiles)
    
    data = pd.concat([data, dataFiles], axis=1)
    data["question"] = question
    data["answer"] = response

    # Sends dataset to OpenScale datamart ONLY NEEDED IF you are not using a deployed wx.ai endpoint.
    #push_record(relevant_chunks, question, response)

    return data

####### MAIN START

app = Flask(__name__)

#Helper Client connection to watsonx.ai
#credentials = {"url": os.getenv("WATSONXAI_ENDPOINT"), "apikey": os.getenv("APIKEY")}
#client = wxAPIClient(credentials)
#client.set.default_project(os.getenv("PROJECT_ID"))

#Helper Client connection to watsonx.governance
#wos_client, payload_logging_data_set_id = getOpenScaleCreds()

@app.route("/generate_results", methods=["POST"])
def generate_results():
    """
    This function handles the POST request to generate results.

    Parameters:
    request (flask.Request): The incoming request object containing the JSON data.

    Returns:
    flask.Response: A JSON response containing the results of the prediction.
    """
    # Get the input parameters from the request
    data = request.json
    # Call the predict function to generate results
    result = ask_question(data.get("question"))

    # Convert the result DataFrame to JSON format and return the response
    return result.to_json(orient="records")


if __name__ == "__main__":
    """
    This is the main executable that sets up the necessary credentials, initializes the embeddings and LLM model,
    and then starts a Flask server to handle POST requests for generating results.
    """
    app.run(host="0.0.0.0", port=5001)
