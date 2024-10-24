# My Streamlit Sample App

This is a sample app as a template for you to quickly develop a user interface when interacting with the WatsonX LLMs through API

## Prerequisites

- ** Python 3.11 or higher **
  

## Prepare Python Evnironment

1. Create a virtual environment

```bash
python -m venv venv
```

2. Activate the virtual environment
   - Windows
    ```bash
    venv\Scripts\activate
    ```
   - macOS or Linux
    ```bash
    source venv/bin/activate
    ``` 

3. Install the required dependencies
   ```bash
   pip install -r requirements.txt
   ```

## Running the App
```bash
streamlit run src/mystreamlit.py
```

This will launch the app in your default web browser. If it doesn't open automatically, navigate to http://localhost:8501 in your browser.


## (Optional) WatsonX AI API Call

If you plan to use WatsonX AI API calls, `src/watsonxai.py` has the skeleton for invoking the WatsonX APIs.

### Update the API related variables
The vairables are configured in `.env`, please change it accordingly.

```
WX_URL=https://us-south.ml.cloud.ibm.com
WX_API_KEY=<your api key, refer to the link below to get API Key>
WX_PROJECT_ID=<your project id in watsonx.ai>
WX_MODEL_ID=<Model Id of your choice>
```

- Quick Start on [watsonx Developer Hub](https://www.ibm.com/watsonx/developer/get-started/quick-start)
- Generate A new API Key [Here](https://cloud.ibm.com/docs/account?topic=account-userapikey&interface=ui)
- Find the available models [Here](https://www.ibm.com/watsonx/developer/get-started/models)