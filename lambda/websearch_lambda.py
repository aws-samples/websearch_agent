# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import http.client
import json
import logging
import os
import urllib.parse
import urllib.request

import boto3

log_level = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
logging.basicConfig(format="[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
ACTION_GROUP_NAME = os.environ.get("ACTION_GROUP", "action-group-web-search-d213q")
FUNCTION_NAMES = ["tavily-ai-search", "google-search"]


def is_env_var_set(env_var: str) -> bool:
    return env_var in os.environ and os.environ[env_var] not in ("", "0", "false", "False")


def get_from_secretstore_or_env(key: str) -> str:
    if is_env_var_set(key):
        logger.warning(f"getting value for {key} from environment var; recommended to use AWS Secrets Manager instead")
        return os.environ[key]

    session = boto3.session.Session()
    secrets_manager = session.client(service_name="secretsmanager", region_name=AWS_REGION)
    try:
        secret_value = secrets_manager.get_secret_value(SecretId=key)
    except Exception as e:
        logger.error(f"could not get secret {key} from secrets manager: {e}")
        raise e

    secret: str = secret_value["SecretString"]

    return secret


SERPER_API_KEY = get_from_secretstore_or_env("SERPER_API_KEY")
TAVILY_API_KEY = get_from_secretstore_or_env("TAVILY_API_KEY")


def extract_search_params(action_group, function, parameters):
    if action_group != ACTION_GROUP_NAME:
        logger.error(f"unexpected name '{action_group}'; expected valid action group name '{ACTION_GROUP_NAME}'")
        return None, None

    if function not in FUNCTION_NAMES:
        logger.error(f"unexpected function name '{function}'; valid function names are'{FUNCTION_NAMES}'")
        return None, None

    search_query = next(
        (param["value"] for param in parameters if param["name"] == "search_query"),
        None,
    )

    target_website = next(
        (param["value"] for param in parameters if param["name"] == "target_website"),
        None,
    )

    logger.debug(f"extract_search_params: {search_query=} {target_website=}")

    return search_query, target_website


def google_search(search_query: str, target_website: str = "") -> str:
    query = search_query
    if target_website:
        query += f" site:{target_website}"

    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({"q": query})
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

    search_type = "news"  # "news", "search",
    conn.request("POST", f"/{search_type}", payload, headers)
    res = conn.getresponse()
    data = res.read()

    return data.decode("utf-8")


def tavily_ai_search(search_query: str, target_website: str = "") -> str:
    logger.info(f"executing Tavily AI search with {search_query=}")

    base_url = "https://api.tavily.com/search"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": search_query,
        "search_depth": "advanced",
        "include_images": False,
        "include_answer": False,
        "include_raw_content": False,
        "max_results": 3,
        "include_domains": [target_website] if target_website else [],
        "exclude_domains": [],
    }

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(base_url, data=data, headers=headers)  # nosec: B310 fixed url we want to open

    try:
        response = urllib.request.urlopen(request)  # nosec: B310 fixed url we want to open
        response_data: str = response.read().decode("utf-8")
        logger.debug(f"response from Tavily AI search {response_data=}")
        return response_data
    except urllib.error.HTTPError as e:
        logger.error(f"failed to retrieve search results from Tavily AI Search, error: {e.code}")

    return ""


def lambda_handler(event, _):  # type: ignore
    logging.debug(f"lambda_handler {event=}")

    action_group = event["actionGroup"]
    function = event["function"]
    parameters = event.get("parameters", [])

    logger.info(f"lambda_handler: {action_group=} {function=}")

    search_query, target_website = extract_search_params(action_group, function, parameters)

    search_results: str = ""
    if function == "tavily-ai-search":
        search_results = tavily_ai_search(search_query, target_website)
    elif function == "google-search":
        search_results = google_search(search_query, target_website)

    logger.debug(f"query results {search_results=}")

    # Prepare the response
    function_response_body = {"TEXT": {"body": f"Here are the top search results for the query '{search_query}': {search_results} "}}

    action_response = {
        "actionGroup": action_group,
        "function": function,
        "functionResponse": {"responseBody": function_response_body},
    }

    response = {"response": action_response, "messageVersion": event["messageVersion"]}

    logger.debug(f"lambda_handler: {response=}")

    return response
