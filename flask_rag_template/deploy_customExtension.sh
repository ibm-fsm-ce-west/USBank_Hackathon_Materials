export RESOURCE_GROUP="cloud resource group"
export CONTAINER_REGISTRY_NAMESPACE="container registry namespace"
export CODE_ENGINE_PROJECT_NAME="container registry project"
export CONTAINER_REGISTRY_SECRET_NAME="customextension-registry"
export APIKEY="Your IBM Cloud API Key"
export REGION="us-south"
export IMAGE_NAME="customextension"

ibmcloud login --apikey $APIKEY -g $RESOURCE_GROUP
ibmcloud cr region-set $REGION
ibmcloud cr login

docker tag $IMAGE_NAME  us.icr.io/$CONTAINER_REGISTRY_NAMESPACE/$IMAGE_NAME:v1
docker push us.icr.io/$CONTAINER_REGISTRY_NAMESPACE/$IMAGE_NAME:v1

ibmcloud ce project select -n $CODE_ENGINE_PROJECT_NAME
ibmcloud ce registry create --name $CONTAINER_REGISTRY_SECRET_NAME --server us.icr.io --username iamapikey --password $APIKEY

ibmcloud ce application create \
--name $IMAGE_NAME \
--image us.icr.io/$CONTAINER_REGISTRY_NAMESPACE/$IMAGE_NAME:v1 \
--registry-secret $CONTAINER_REGISTRY_SECRET_NAME  \
--min 1 \
--cpu 4 \
-m 8G \
--request-timeout 600 \
 --port 5001 