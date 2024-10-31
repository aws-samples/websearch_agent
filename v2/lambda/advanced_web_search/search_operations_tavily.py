import json
import logging
import os
import boto3
from botocore.exceptions import ClientError
import asyncio
from typing import List
from tavily import AsyncTavilyClient
from models import TavilySearchResult

from utils import get_from_secretstore_or_env

logger = logging.getLogger(__name__)

AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")


def get_tavily_api_key():
    return get_from_secretstore_or_env("TAVILY_API_KEY", AWS_REGION)


async def perform_tavily_searches(queries: List[str]) -> List[TavilySearchResult]:
    """
    Performs asynchronous searches using the Tavily API for multiple queries.

    Args:
        queries (List[str]): A list of search queries to process.

    Returns:
        List[TavilySearchResult]: A list of TavilySearchResult objects containing the search results
        for each query. Each result includes the original query, search results, and result count.
        The Pydantic object is defined in models.py

    Example:
        queries = ["tesla news", "AI advances"]
        results = await perform_tavily_searches(queries)
    """
    tavily_api_key = get_tavily_api_key()
    client = AsyncTavilyClient(api_key=tavily_api_key)
    tasks = [search_tavily(client, query) for query in queries]
    return await asyncio.gather(*tasks)


async def search_tavily(client: AsyncTavilyClient, query: str) -> TavilySearchResult:
    """
    Performs a single search using the Tavily API client.
    Args:
        client (AsyncTavilyClient): The initialized Tavily API client instance
        query (str): The search query string to process

    Returns:
        TavilySearchResult: A TavilySearchResult object containing:
            - query: The original search query
            - results: List of search results (empty list if error)
            - count: Number of results found (0 if error)

    The search is configured to:
        - Use "advanced" search depth
        - Exclude images
        - Exclude answer summaries
        - Exclude raw content
        - Return maximum 3 results

    If an error occurs during the API request, it will be logged and an empty
    result will be returned rather than raising an exception.
    """
    try:
        response = await client.search(
            query=query,
            search_depth="advanced",
            include_images=False,
            include_answer=False,
            include_raw_content=False,
            max_results=3,
        )
        return TavilySearchResult(
            query=query,
            results=response.get("results", []),
            count=len(response.get("results", [])),
        )
    except Exception as e:
        logger.error(f"Error during Tavily API request for query '{query}': {str(e)}")
        return TavilySearchResult(query=query, results=[], count=0)
