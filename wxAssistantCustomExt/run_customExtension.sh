#!/bin/sh
docker stop custom_extension_container
docker rm custom_extension_container
docker run --platform linux/amd64 -dit --name custom_extension_container -p 5001:5001 customextension