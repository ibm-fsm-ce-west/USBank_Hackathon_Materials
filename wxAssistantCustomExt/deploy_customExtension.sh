export RESOURCE_GROUP="txv-itz-l4axg3_671281582"
export CONTAINER_REGISTRY_NAMESPACE="cr-txv-itz-l4axg3_671281582"
export CONTAINER_REGISTRY_SECRET_NAME="customextension-registry5"
export APIKEY="49J07H5QPu3uQq64x4fMJsponHfRtHFPHulPDVA-XqSf"
export REGION="us-south"
export IMAGE_NAME="customextension"

ibmcloud login --apikey $APIKEY -g $RESOURCE_GROUP
ibmcloud cr region-set $REGION
ibmcloud cr login

docker tag $IMAGE_NAME  us.icr.io/$CONTAINER_REGISTRY_NAMESPACE/$IMAGE_NAME:v1
docker push us.icr.io/$CONTAINER_REGISTRY_NAMESPACE/$IMAGE_NAME:v1

ibmcloud target -g watsonx
ibmcloud ce project select -n "Code Engine-itz"
ibmcloud ce registry create --name $CONTAINER_REGISTRY_SECRET_NAME --server us.icr.io --username iamapikey --password $APIKEY
#ibmcloud ce application update  --name generate-results


ibmcloud ce application create \
--name $IMAGE_NAME \
--image us.icr.io/$CONTAINER_REGISTRY_NAMESPACE/$IMAGE_NAME:v1 \
--registry-secret $CONTAINER_REGISTRY_SECRET_NAME  \
--min 1 \
--cpu 4 \
-m 8G \
--request-timeout 600 \
 --port 5001 