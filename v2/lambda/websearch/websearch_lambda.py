# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import json
from typing import Dict, Any, Optional

from utils import logger, get_from_secretstore_or_env
from models import SearchEvent, SearchResponse
from search_providers import TavilySearchProvider, GoogleSearchProvider
from config import AWS_REGION, ACTION_GROUP_NAME, FUNCTION_NAMES
from validators import validate_search_params
from response_formatter import format_lambda_response
from exceptions import SearchError, ConfigurationError, APIError


# Initialize API keys
SERPER_API_KEY = get_from_secretstore_or_env("SERPER_API_KEY", AWS_REGION)
TAVILY_API_KEY = get_from_secretstore_or_env("TAVILY_API_KEY", AWS_REGION)

# Initialize search providers
tavily_provider = TavilySearchProvider(TAVILY_API_KEY)
google_provider = GoogleSearchProvider(SERPER_API_KEY)


def extract_search_params(action_group, function, parameters):
    if action_group != ACTION_GROUP_NAME:
        logger.error(
            f"unexpected name '{action_group}'; expected valid action group name '{ACTION_GROUP_NAME}'"
        )
        return None, None, None, None, None

    if function not in FUNCTION_NAMES:
        logger.error(
            f"unexpected function name '{function}'; valid function names are'{FUNCTION_NAMES}'"
        )
        return None, None, None, None, None

    # Extract all parameters with defaults
    search_query = next(
        (param["value"] for param in parameters if param["name"] == "search_query"),
        None,
    )
    target_website = next(
        (param["value"] for param in parameters if param["name"] == "target_website"),
        None,
    )

    if function == "tavily-ai-search":
        search_depth = next(
            (param["value"] for param in parameters if param["name"] == "search_depth"),
            "advanced",
        )
        max_results = int(
            next(
                (
                    param["value"]
                    for param in parameters
                    if param["name"] == "max_results"
                ),
                "3",
            )
        )
        topic = next(
            (param["value"] for param in parameters if param["name"] == "topic"),
            "general",
        )
        logger.debug(
            f"extract_search_params Tavily: {search_query=} {target_website=} {search_depth=} {max_results=} {topic=}"
        )
        return search_query, target_website, search_depth, max_results, topic
    else:  # google-search
        search_type = next(
            (param["value"] for param in parameters if param["name"] == "search_type"),
            "search",
        )
        time_period = next(
            (param["value"] for param in parameters if param["name"] == "time_period"),
            None,
        )
        country_code = next(
            (param["value"] for param in parameters if param["name"] == "country_code"),
            "us",
        )
        logger.debug(
            f"extract_search_params Google: {search_query=} {target_website=} {search_type=} {time_period=} {country_code=}"
        )
        return search_query, target_website, search_type, time_period, country_code


def tavily_ai_search(
    search_query: str,
    target_website: Optional[str] = None,
    search_depth: str = "advanced",
    max_results: int = 3,
    topic: str = "general",
    days: int = 3,
) -> Dict[str, Any]:
    logger.info(f"executing Tavily AI search with {search_query=}")
    try:
        return tavily_provider.search(
            search_query, target_website, search_depth, max_results, topic, days
        )
    except Exception as e:
        logger.error(
            f"failed to retrieve search results from Tavily AI Search: {str(e)}"
        )
        return {"error": str(e)}


def lambda_handler(event, _):  # type: ignore
    logger.debug(f"lambda_handler {event=}")
    logger.debug(f"full event {event}")

    action_group = event["actionGroup"]
    function = event["function"]
    parameters = event.get("parameters", [])

    logger.info(f"lambda_handler: {action_group=} {function=}")

    search_query, target_website, search_depth, max_results, topic = (
        extract_search_params(action_group, function, parameters)
    )

    search_results = {}
    if function == "tavily-ai-search":
        search_results = tavily_ai_search(
            search_query, target_website, search_depth, max_results, topic
        )
    elif function == "google-search":
        search_query, target_website, search_type, time_period, country_code = (
            extract_search_params(action_group, function, parameters)
        )
        try:
            search_results = google_provider.search(
                search_query, target_website, search_type, time_period, country_code
            )
        except SearchError as e:
            logger.error(f"Google search failed: {str(e)}")
            search_results = {"error": str(e)}

    logger.debug(f"query results {search_results=}")

    # Prepare the response
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

    response = {"response": action_response, "messageVersion": event["messageVersion"]}

    logger.debug(f"lambda_handler: {response=}")

    return response
