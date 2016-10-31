#!/bin/bash

# Gaia environment: dev, prod or other
if [ -z "$ENV" ]; then
  ENV=dev
fi

if [ -z "$AWS_DEFAULT_REGION" ]; then
  export AWS_REGION="$(aws configure get region)"
else
  export AWS_REGION="$AWS_DEFAULT_REGION"
fi
