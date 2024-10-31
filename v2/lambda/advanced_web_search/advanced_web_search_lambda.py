import json
import logging
import os
import asyncio
from models import (
    InitialQuery,
    AggregatedSearchResults,
    AdvancedWebSearchResult,
    FinalAnswer,
)
from llm_operations import rewrite_query, analyze_results, formulate_final_answer
from search_operations_tavily import perform_tavily_searches

log_level = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
logging.basicConfig(
    format="[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

ACTION_GROUP_NAME = os.environ.get("ACTION_GROUP", "action-group-advanced-web-search")
FUNCTION_NAME = "advanced-web-search"


async def advanced_web_search(search_query: str) -> AdvancedWebSearchResult:
    """
    Performs an advanced web search with iterative query refinement and result analysis.

    This async function takes a search query and iteratively:
    1. Rewrites the query into multiple variations
    2. Performs searches using the Tavily search API
    3. Analyzes the aggregated results
    4. Either returns a final answer or refines the query for another iteration

    Args:
        search_query (str): The initial search query string

    Returns:
        AdvancedWebSearchResult: Object containing:
            - original_query: The initial search query
            - final_answer: FinalAnswer object with the answer and references
            - search_iterations: Number of search iterations performed
            - total_queries: Total number of queries executed
            - total_results: Total number of results retrieved

    The function will attempt up to 3 iterations of query refinement. If no satisfactory
    answer is found after 3 iterations, it returns a result indicating the failure to
    find an answer.
    """
    initial_query = InitialQuery(query=search_query)
    iterations = 0
    max_iterations = 3
    total_queries = 0
    total_results = 0

    while iterations < max_iterations:
        iterations += 1
        rewritten_queries = rewrite_query(initial_query)
        new_queries = rewritten_queries.rewritten_queries
        tavily_results = await perform_tavily_searches(new_queries)

        total_queries += len(new_queries)
        total_results += sum(result.count for result in tavily_results)

        aggregated_results = AggregatedSearchResults(
            original_query=initial_query.query,
            rewritten_queries=new_queries,
            search_results=tavily_results,
        )
        analysis = analyze_results(aggregated_results)

        if analysis.is_question_answered:
            final_answer = formulate_final_answer(aggregated_results)
            return AdvancedWebSearchResult(
                original_query=initial_query.query,
                final_answer=final_answer,
                search_iterations=iterations,
                total_queries=total_queries,
                total_results=total_results,
            )

        initial_query = InitialQuery(query=analysis.explanation)

    return AdvancedWebSearchResult(
        original_query=search_query,
        final_answer=FinalAnswer(
            original_query=search_query,
            answer="Unable to find a satisfactory answer after multiple attempts",
            references=[],
        ),
        search_iterations=iterations,
        total_queries=total_queries,
        total_results=total_results,
    )


async def async_lambda_handler(event, context):
    """
    Handles Lambda function invocations for advanced web search requests.

    This async function processes incoming Lambda events containing web search queries,
    executes the search using the advanced_web_search function, and formats the results
    into the expected response structure.
    Args:
        event (dict): AWS Lambda event object containing:
            - actionGroup: The action group identifier
            - function: The function name
            - parameters: List of parameters including search_query
            - messageVersion: Message format version
        context: AWS Lambda context object (unused)

    Returns:
        dict: Response object containing:
            - response: Action response with search results
            - messageVersion: Message format version from input event

    Raises:
        Exception: Any errors during execution are caught, logged and returned as error responses
    """
    logging.debug(f"lambda_handler {event=}")

    try:
        action_group = event["actionGroup"]
        function = event["function"]
        parameters = event.get("parameters", [])

        logger.info(f"lambda_handler: {action_group=} {function=}")

        search_query = next(
            (param["value"] for param in parameters if param["name"] == "search_query"),
            None,
        )

        if search_query:
            search_results = await advanced_web_search(search_query)
            result_text = json.dumps(search_results.dict(), indent=2)
        else:
            result_text = "Error: Invalid search query"

        logger.debug(f"query results {result_text=}")

        function_response_body = {
            "TEXT": {
                "body": f"Here are the advanced web search results for the query '{search_query}':\n{result_text}"
            }
        }

        action_response = {
            "actionGroup": action_group,
            "function": function,
            "functionResponse": {"responseBody": function_response_body},
        }

        response = {
            "response": action_response,
            "messageVersion": event["messageVersion"],
        }

        logger.debug(f"lambda_handler: {response=}")

        return response

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return {
            "response": {
                "actionGroup": ACTION_GROUP_NAME,
                "function": FUNCTION_NAME,
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": f"An error occurred while processing the request: {str(e)}"
                        }
                    }
                },
            },
            "messageVersion": event.get("messageVersion", "1.0"),
        }


def lambda_handler(event, context):
    """
    Main Lambda handler function that executes the async_lambda_handler.

    This function serves as a synchronous wrapper around the asynchronous
    async_lambda_handler, using asyncio.run to execute the async function
    in a synchronous context as required by AWS Lambda.

    Args:
        event (dict): AWS Lambda event object containing the request details
        context: AWS Lambda context object

    Returns:
        dict: The response from async_lambda_handler containing the search results
              or error information
    """
    return asyncio.run(async_lambda_handler(event, context))
