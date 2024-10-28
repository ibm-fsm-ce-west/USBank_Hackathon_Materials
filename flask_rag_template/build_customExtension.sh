#!/bin/sh
DOCKER_BUILDKIT=1 docker build --no-cache \
    --secret "id=secretfile1,src=.env" \
    -t customextension \
    -f Dockerfile .