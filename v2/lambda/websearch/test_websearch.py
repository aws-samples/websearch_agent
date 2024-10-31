import json
from websearch_lambda import lambda_handler

# Mock event based on the provided test event
mock_event = {
    "messageVersion": "1.0",
    "function": "tavily-ai-search",
    "parameters": [
        {
            "name": "search_query",
            "type": "string",
            "value": "Latest developments in quantum computing",
        },
        {
            "name": "search_depth",
            "type": "string",
            "value": "advanced",
        },
        {
            "name": "max_results",
            "type": "number",
            "value": "3",
        },
        {
            "name": "topic",
            "type": "string",
            "value": "general",
        }
    ],
    "sessionId": "510646607739287",
    "agent": {
        "name": "websearch_agent",
        "version": "DRAFT",
        "id": "Y3JFGHUJ6H",
        "alias": "TSTALIASID",
    },
    "actionGroup": "action-group-web-search-d213q",
    "sessionAttributes": {},
    "promptSessionAttributes": {},
    "inputText": "Search for latest developments in quantum computing",
}

# Mock context object
class MockContext:
    def __init__(self):
        self.function_name = "test_websearch"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = (
            "arn:aws:lambda:us-west-2:123456789012:function:test_websearch"
        )

# Create an instance of the mock context
mock_context = MockContext()

def test_websearch():
    # Call the lambda_handler function with mock event and context
    response = lambda_handler(mock_event, mock_context)

    # Print the response
    print(json.dumps(response, indent=2))

    # Add assertions here to verify the response structure and content
    assert "response" in response
    assert "actionGroup" in response["response"]
    assert "function" in response["response"]
    assert "functionResponse" in response["response"]
    assert "responseBody" in response["response"]["functionResponse"]
    assert "TEXT" in response["response"]["functionResponse"]["responseBody"]
    assert "body" in response["response"]["functionResponse"]["responseBody"]["TEXT"]

if __name__ == "__main__":
    test_websearch()
