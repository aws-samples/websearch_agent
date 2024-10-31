import json
import http.client
import urllib.request
import urllib.parse
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from utils import logger
from exceptions import APIError

class SearchProvider(ABC):
    @abstractmethod
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    @abstractmethod
    def search(
        self, 
        query: str, 
        target_website: Optional[str] = None,
        search_type: str = "search",
        **kwargs
    ) -> Dict[str, Any]:
        pass

class TavilySearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(
        self, 
        query: str, 
        target_website: Optional[str] = None,
        search_depth: str = "advanced",
        max_results: int = 3,
        topic: str = "general", 
        days: int = 3,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        logger.info(f"Executing Tavily AI search with query={query}")
        
        base_url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "max_results": max_results,
            "include_images": include_images,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "include_domains": [target_website] if target_website else [],
            "exclude_domains": [],
        }
        
        # Only add days parameter if topic is news
        if topic == "news" and days:
            payload["days"] = days

        try:
            data = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(base_url, data=data, headers=headers)
            response = urllib.request.urlopen(request)
            response_data = json.loads(response.read().decode("utf-8"))
            logger.debug(f"Response from Tavily AI search: {response_data}")
            return response_data
        except Exception as e:
            logger.error(f"Failed to retrieve search results from Tavily AI Search: {str(e)}")
            raise APIError(f"Tavily AI Search error: {str(e)}")

class GoogleSearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(
        self,
        query: str,
        target_website: Optional[str] = None,
        search_type: str = "search",
        time_period: Optional[str] = None,
        country_code: str = "us",
        **kwargs
    ) -> Dict[str, Any]:
        logger.info(f"Executing Google search with query={query}")
        
        if target_website:
            query = f"site:{target_website} {query}"

        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = {"q": query, "gl": country_code}

        if time_period:
            payload["tbs"] = time_period

        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

        try:
            conn.request("POST", f"/{search_type}", json.dumps(payload), headers)
            res = conn.getresponse()
            data = res.read()
            response = json.loads(data.decode("utf-8"))

            if res.status != 200:
                error_msg = f"API request failed with status code {res.status}: {response.get('message', 'Unknown error')}"
                logger.error(error_msg)
                raise APIError(error_msg)

            return self._process_response(response, search_type)
        except Exception as e:
            logger.error(f"Failed to retrieve search results from Google Search: {str(e)}")
            raise APIError(f"Google Search error: {str(e)}")
        finally:
            conn.close()

    def _process_response(self, response: Dict[str, Any], search_type: str) -> Dict[str, Any]:
        processed_results = []

        if search_type == "search":
            organic = response.get("organic", [])
            for result in organic:
                processed_results.append({
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet"),
                    "position": result.get("position"),
                })
        elif search_type == "news":
            news = response.get("news", [])
            for result in news:
                processed_results.append({
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet"),
                    "date": result.get("date"),
                    "source": result.get("source"),
                })

        return {
            "searchMetadata": {
                "query": response.get("searchParameters", {}).get("q"),
                "totalResults": response.get("searchInformation", {}).get("totalResults"),
            },
            "results": processed_results,
        }
