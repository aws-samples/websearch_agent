import json
from typing import Dict, Any

def format_lambda_response(
    action_group: str,
    function: str,
    search_query: str,
    search_results: Dict[str, Any],
    message_version: str
) -> Dict[str, Any]:
    function_response_body = {
        "TEXT": {
            "body": f"Here are the top search results for the query '{search_query}': {json.dumps(search_results)} "
        }
    }

    action_response = {
        "actionGroup": action_group,
        "function": function,
        "functionResponse": {"responseBody": function_response_body},
    }

    return {
        "response": action_response, 
        "messageVersion": message_version
    }
