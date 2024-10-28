## Welcome to the RAG-capable Flask Application Template

To execute the code, you will first need to set up the necessary environment variables in .env.

Next, you will need to install the necessary dependencies from requirements.txt:

```
python -m venv myvenv
source myenv/bin/activate
pip install -r requirements.txt
```

Then, _add any text or pdf files you wish to embed into watsonx Discovery for RAG into the knowledge_base folder_. If you wish to update these after embedding, you will need to either delete the previous index or simply change its name (found in .env) to a new one.

Finally, run locally:

```
python customExtension.py
```

or in a container:

```
./build_customExtension.sh
./run_customExtension.sh
```

to deploy this app to Code Engine, first replace the environment variables located in deploy_customExtension.sh, and then run it:

```
./deploy_customExtension.sh
```

To ask questions, hit the /generate_results endpoint. When running locally, your curl command will look like:

```
curl -X POST http://localhost:5001/generate_results -H "Content-Type: application/json" -d '{"question": "Your question here"}'
```

When in a container, replace localhost with the container's endpoint.

The code includes a main executable section that sets up the necessary credentials and starts a Flask server to handle POST requests for generating results.

Please note that the code provided is a complex and comprehensive implementation, and it may require further customization and modification to fit your specific requirements. It is recommended to review and understand the code thoroughly before using it in a production environment.