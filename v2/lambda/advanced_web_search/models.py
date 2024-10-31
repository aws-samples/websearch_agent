from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class InitialQuery(BaseModel):
    query: str = Field(..., description="The initial query from the human user")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the latest developments in quantum computing?"
            }
        }


class RewrittenQueries(BaseModel):
    original_query: str = Field(..., description="The original query")
    rewritten_queries: List[str] = Field(
        ...,
        description="List of rewritten queries generated to improve diversity and quality of the search results",
    )


class TavilySearchQuery(BaseModel):
    query: str = Field(..., description="The search query")
    search_depth: str = Field("advanced", description="The depth of the search")
    include_images: bool = Field(
        False, description="Whether to include images in the results"
    )
    include_answer: bool = Field(
        False, description="Whether to include an answer in the results"
    )
    include_raw_content: bool = Field(
        False, description="Whether to include raw content in the results"
    )
    max_results: int = Field(3, description="The maximum number of results to return")
    include_domains: List[str] = Field(
        [], description="List of domains to include in the search"
    )
    exclude_domains: List[str] = Field(
        [], description="List of domains to exclude from the search"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Recent breakthroughs in quantum computing technology",
                "search_depth": "advanced",
                "include_images": False,
                "include_answer": False,
                "include_raw_content": False,
                "max_results": 3,
                "include_domains": [],
                "exclude_domains": [],
            }
        }


class TavilySearchResult(BaseModel):
    query: str = Field(..., description="The search query used")
    results: List[Dict[str, Any]] = Field(..., description="List of search results")
    count: int = Field(..., description="Number of results returned")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Recent breakthroughs in quantum computing technology",
                "results": [
                    {
                        "title": "Latest Quantum Computing Breakthroughs",
                        "url": "https://example.com/quantum-breakthroughs",
                        "content": "Summary of recent quantum computing advancements...",
                    }
                ],
                "count": 1,
            }
        }


class AggregatedSearchResults(BaseModel):
    original_query: str = Field(..., description="The original query")
    rewritten_queries: List[str] = Field(..., description="List of rewritten queries")
    search_results: List[TavilySearchResult] = Field(
        ..., description="List of search results for each query"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "original_query": "What are the latest developments in quantum computing?",
                "rewritten_queries": [
                    "Recent breakthroughs in quantum computing technology",
                    "Current state of quantum computing research and applications",
                ],
                "search_results": [
                    {
                        "query": "Recent breakthroughs in quantum computing technology",
                        "results": [
                            {
                                "title": "Latest Quantum Computing Breakthroughs",
                                "url": "https://example.com/quantum-breakthroughs",
                                "content": "Summary of recent quantum computing advancements...",
                            }
                        ],
                        "count": 1,
                    }
                ],
            }
        }


class LLMAnalysisResult(BaseModel):
    is_question_answered: bool = Field(
        ..., description="Whether the question is sufficiently answered"
    )
    explanation: str = Field(..., description="Explanation of the analysis")

    class Config:
        json_schema_extra = {
            "example": {
                "is_question_answered": True,
                "explanation": "The search results provide comprehensive information on recent quantum computing developments, including breakthroughs in error correction and quantum supremacy demonstrations.",
            }
        }


class FinalAnswer(BaseModel):
    original_query: str = Field(..., description="The original query")
    answer: str = Field(..., description="The final answer to the query")
    references: List[Dict[str, str]] = Field(
        ..., description="List of references used in the answer"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "original_query": "What are the latest developments in quantum computing?",
                "answer": "Recent developments in quantum computing include significant progress in error correction techniques and demonstrations of quantum supremacy by major tech companies...",
                "references": [
                    {
                        "title": "Latest Quantum Computing Breakthroughs",
                        "url": "https://example.com/quantum-breakthroughs",
                    }
                ],
            }
        }


class AdvancedWebSearchResult(BaseModel):
    original_query: str = Field(..., description="The original query")
    final_answer: Optional[FinalAnswer] = Field(
        None, description="The final answer, if available"
    )
    search_iterations: int = Field(
        ..., description="Number of search iterations performed"
    )
    total_queries: int = Field(..., description="Total number of queries made")
    total_results: int = Field(..., description="Total number of results obtained")

    class Config:
        json_schema_extra = {
            "example": {
                "original_query": "What are the latest developments in quantum computing?",
                "final_answer": {
                    "original_query": "What are the latest developments in quantum computing?",
                    "answer": "Recent developments in quantum computing include significant progress in error correction techniques and demonstrations of quantum supremacy by major tech companies...",
                    "references": [
                        {
                            "title": "Latest Quantum Computing Breakthroughs",
                            "url": "https://example.com/quantum-breakthroughs",
                        }
                    ],
                },
                "search_iterations": 2,
                "total_queries": 3,
                "total_results": 5,
            }
        }
