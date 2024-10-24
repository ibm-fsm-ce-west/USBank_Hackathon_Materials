import os
import re
import requests
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from ibm_watsonx_ai.foundation_models.utils.enums import DecodingMethods


class WatsonxAIWrapper:

    def __init__(self):
        load_dotenv()

        credentials = Credentials(
                        url = os.getenv("WX_URL"),
                        api_key = os.getenv("WX_API_KEY")
                        )

        client = APIClient(credentials)

        gen_parms = {
            GenParams.DECODING_METHOD: DecodingMethods.SAMPLE,
            GenParams.MAX_NEW_TOKENS: 100
        }
        # client.foundation_models.TextModels.show()
        model_id = os.getenv("WX_MODEL_ID")
        project_id = os.getenv("WX_PROJECT_ID")
        space_id = None
        verify = False

        self.model = ModelInference(
        model_id=model_id,
        credentials=credentials,
        params=gen_parms,
        project_id=project_id,
        space_id=space_id,
        verify=verify,
        )

        self.gen_parms_override = gen_parms = {
            GenParams.DECODING_METHOD: DecodingMethods.GREEDY,
            GenParams.REPETITION_PENALTY: 1,
            GenParams.MAX_NEW_TOKENS: 1000
        }



    def call_wx_api(self, prompt: str) -> str:
        print(f">> Calling LLM: {prompt}")
        prompt_template=f"Input: {prompt} \n Output:"
        generated_response = self.model.generate(prompt=prompt_template, params=self.gen_parms_override)
        result = generated_response
        print(f"<< LLM Call Response: \n {result}")
        print("---" * 15)
        return result["results"][0]["generated_text"]
