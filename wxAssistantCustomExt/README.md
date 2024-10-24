# Custom Extension for WatsonX Assistant/Orchestrate

**The High Level Steps for Developing an Extension**
1. Build your application (`src/customExtension.py` is an sample app using Flask)
2. Build Docker image (sample `Dockerfile` and some supporting shell scripts can be found in current folder)
3. Deploy the Docker image to Code Engine
- Upload to IBM Cloud Container Registry
- Run the app in Code Engine
4. Build the OpenAPI Specification (sample file attached `customExtensionOpenAPISpec.json`)
5. Import the OpenAPI Specification json file in WatsonX Assistant
6. Start using the extension


## Build a Flask App
The sample Flask python file `src/customExtension.py`.
