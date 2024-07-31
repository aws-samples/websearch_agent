# Web Search Agent with Amazon Bedrock

This repository contains the code for implementing a web search agent using Amazon Bedrock, as described in the AWS blog post "How to use Amazon Bedrock agents with a web search API to integrate dynamic web content in your generative AI application."

## Overview

This project demonstrates how to create an AI agent that can perform web searches using Amazon Bedrock. It integrates two web search APIs (SerpAPI and Tavily AI) and showcases how to build and deploy the agent using both the AWS Management Console and AWS CDK.

## Features

- Integration with Amazon Bedrock for AI agent creation
- Web search functionality using SerpAPI (Google Search) and Tavily AI
- AWS CDK deployment script for infrastructure as code
- Lambda function for handling web search requests
- Example of how to use AWS Secrets Manager for API key storage

## Prerequisites

- An active AWS Account
- [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install) version 2.174.3 or later
- Python 3.11 or later
- API keys for [SerpAPI](https://serpapi.com/) and [Tavily AI](https://tavily.com/)

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/aws-samples/websearch_agent
   ```

2. Create and activate a Python virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Store your API keys in AWS Secrets Manager:
   ```
   aws secretsmanager create-secret --name SERPER_API_KEY --secret-string "your_serper_api_key"
   aws secretsmanager create-secret --name TAVILY_API_KEY --secret-string "your_tavily_api_key"
   ```

5. Deploy the CDK stack:
   ```
   cdk deploy
   ```

## Usage

After deployment, you can test the agent using the provided Python script:

```
python invoke-agent.py --agent_id <agent_id> --agent_alias_id <agent_alias_id> --prompt "What are the latest AWS news?"
```

Replace `<agent_id>` and `<agent_alias_id>` with the values output by the CDK deployment.

## Project Structure

- `/app.py`: Top-level definition of the AWS CDK app
- `/cdk/`: Contains the stack definition for the web search agent
- `/lambda/`: Contains the Lambda function code for handling API calls
- `/test/`: Contains a Python script to test the deployed agent

## Cleaning Up

To remove all resources created by this project:

1. Run `cdk destroy` to delete the CDK-managed resources.
2. Delete the secrets from AWS Secrets Manager:
   ```
   aws secretsmanager delete-secret --secret-id SERPER_API_KEY
   aws secretsmanager delete-secret --secret-id TAVILY_API_KEY
   ```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file for details.
