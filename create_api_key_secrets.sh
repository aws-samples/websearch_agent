#!/bin/bash

echo "Ensure TAVILY_API_KEY and SERPER_API_KEY environment variables are set."

echo "Creating SERPER_API_KEY secret in secrets manager..."
aws secretsmanager create-secret \
    --name SERPER_API_KEY \
    --description "The API secret key for Serper." \
    --secret-string "$SERPER_API_KEY"

echo "Creating TAVILY_API_KEY secret in secrets manager..."
aws secretsmanager create-secret \
    --name TAVILY_API_KEY \
    --description "The API secret key for Tavily AI." \
    --secret-string "$TAVILY_API_KEY"

echo "Done."
