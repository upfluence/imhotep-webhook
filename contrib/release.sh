#!/bin/bash

docker build -t upfluence/imhotep-webhook:latest .
docker push upfluence/imhotep-webhook
