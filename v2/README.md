# Web Search Agent V2 with Amazon Bedrock

This is version 2 of the Web Search Agent, featuring enhanced capabilities and improved architecture. This version introduces advanced web search capabilities, asynchronous operations, and integration with Claude 3 models.

## New Features in V2

- **Advanced Web Search**: Intelligent query rewriting and result analysis
- **Asynchronous Operations**: Parallel search execution for better performance
- **Structured Output**: Integration with Bedrock's Claude 3 models for better response formatting
- **Enhanced Error Handling**: Robust error management and validation
- **Cross-Region Support**: Flexible deployment across AWS regions
- **Type Safety**: Comprehensive type hints and Pydantic models

## Architecture Components

- **Web Search Lambda**: Basic web search functionality using Google Search and Tavily AI
- **Advanced Web Search Lambda**: Enhanced search with query refinement and result analysis
- **Lambda Layers**: Optimized dependency management for ARM64 architecture
- **Bedrock Agent**: Updated agent configuration for improved interaction

## Prerequisites

- An active AWS Account
- AWS CDK version 2.174.3 or later
- Python 3.12 or later
- API keys for [SerpAPI](https://serpapi.com/) and [Tavily AI](https://tavily.com/)

## Setup

1. Clone the repository and follow the setups steps that are the same as in V1.

   ```
   git clone https://github.com/aws-samples/websearch_agent
   cd websearch_agent
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
   cd v2
   cdk deploy
   ```

## Configuration

The `config.yaml` file contains important settings:

- AWS region configuration
- Cross-region inference settings
- Model selection (Claude 3 Sonnet/Haiku)
- Lambda function names and configurations
- Action group names

If you deployed the v1 version, you have 2 options:

- delete the v1 stack
- rename the components in the v2 stack to avoid naming conflicts

## Testing

Test scripts are provided for both web search functions:

- `test/invoke-agent.py`: Test the basic web search

## Cleaning Up

To remove all resources:

1. Run `cdk destroy` to delete the CDK-managed resources
2. Delete the secrets from AWS Secrets Manager:
   ```
   aws secretsmanager delete-secret --secret-id SERPER_API_KEY
   aws secretsmanager delete-secret --secret-id TAVILY_API_KEY
   ```

## Security

See [CONTRIBUTING](../CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the MIT-0 License. See the [LICENSE](../LICENSE) file for details.
