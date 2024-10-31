import logging
import os
from botocore.exceptions import ClientError
from models import (
    InitialQuery,
    RewrittenQueries,
    AggregatedSearchResults,
    LLMAnalysisResult,
    FinalAnswer,
)
from strut_output_bedrock import create_bedrock_structured_output

logger = logging.getLogger(__name__)

SMART_LLM = os.environ.get("SMART_LLM", "anthropic.claude-3-5-sonnet-20240620-v1:0")
FAST_LLM = os.environ.get("FAST_LLM", "anthropic.claude-3-haiku-20240307-v1:0")
AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")


def rewrite_query(initial_query: InitialQuery) -> RewrittenQueries:
    try:
        system_prompt = """
        As an AI language model specializing in query optimization, your task is to rewrite the given search query to improve search results. 
        Follow these guidelines:
        1. Maintain the original intent and core subject of the query.
        2. Expand on any abbreviations or acronyms.
        3. Add relevant context or specificity that might yield better results.
        4. Consider alternative phrasings that might capture different aspects of the topic.

        Your output must be a JSON object with two fields:
        1. 'original_query': The exact query provided to you.
        2. 'rewritten_queries': A list of 3 rewritten versions of the original query.

        Example output format:
        {
            "original_query": "What are quantum computers?",
            "rewritten_queries": [
                "Explain the basic principles and functionality of quantum computing",
                "How do quantum computers differ from classical computers in terms of processing and capabilities?",
                "Recent advancements and potential applications of quantum computing technology"
            ]
        }
        """
        rewritten_queries = create_bedrock_structured_output(
            pydantic_model=RewrittenQueries,
            model_id=SMART_LLM,
            temperature=0.7,
            system_prompt=system_prompt,
            region_name=AWS_REGION,
        )

        query_rewrite_prompt = f"Rewrite the following search query to improve search results: <search_query>{initial_query.query}</search_query>"
        logger.debug(f"Query rewrite prompt: {query_rewrite_prompt}")

        result = rewritten_queries.invoke(initial_query.query)
        logger.debug(f"Rewritten queries: {result}")
        return result

    except ClientError as e:
        logger.error(f"Error rewriting query: {e}")
        return RewrittenQueries(
            original_query=initial_query.query, rewritten_queries=[initial_query.query]
        )


def analyze_results(aggregated_results: AggregatedSearchResults) -> LLMAnalysisResult:
    try:
        system_prompt = """
        As an advanced AI analyst specializing in information evaluation, your task is to thoroughly analyze the provided search results and determine if they sufficiently answer the original query. Follow these guidelines:

        1. Comprehension: Carefully read and understand the original query and all search results.
        2. Relevance Assessment: Evaluate how directly each result addresses the query's main points.
        3. Depth of Information: Assess the depth and breadth of information provided in the results.
        4. Credibility: Consider the sources of information and their reliability.
        5. Completeness: Determine if all aspects of the query are addressed in the collective results.
        6. Contradictions: Identify any conflicting information across the results.
        7. Currency: Evaluate if the information is up-to-date and relevant to the current context.

        Your output must be a JSON object with two fields:
        1. 'is_question_answered': A boolean indicating whether the search results sufficiently answer the original query.
        2. 'explanation': A detailed explanation of your analysis, including:
           - Why you believe the question is or is not sufficiently answered.
           - Key points from the search results that support your conclusion.
           - Any gaps in information or areas that require further investigation.
           - Suggestions for refining the search if the question is not fully answered.

        Example output format:
        {
            "is_question_answered": true,
            "explanation": "The search results provide a comprehensive answer to the query about recent developments in quantum computing. Key points include: 1) Breakthrough in error correction techniques by Company X, 2) Demonstration of quantum supremacy by Company Y, and 3) Application of quantum algorithms in drug discovery by Research Institute Z. The information comes from reputable sources and covers both theoretical advancements and practical applications. While the results are sufficient, further investigation into the scalability of these developments could provide additional context."
        }

        Analyze the following search results and provide your assessment:
        """

        analysis = create_bedrock_structured_output(
            pydantic_model=LLMAnalysisResult,
            model_id=SMART_LLM,
            temperature=0.5,
            system_prompt=system_prompt,
            region_name=AWS_REGION,
        )
        return analysis.invoke(aggregated_results.dict())
    except ClientError as e:
        logger.error(f"Error analyzing results: {e}")
        return LLMAnalysisResult(
            is_question_answered=False,
            explanation="Error occurred during analysis. The system encountered an issue while processing the search results. Please try again or refine your query for a new search.",
        )


def formulate_final_answer(aggregated_results: AggregatedSearchResults) -> FinalAnswer:
    try:
        system_prompt = """
        As an advanced AI specializing in information synthesis and summarization, your task is to formulate a comprehensive final answer based on the provided search results. Follow these guidelines:

        1. Comprehension: Thoroughly understand the original query and all search results.
        2. Synthesis: Combine information from multiple sources to create a coherent and comprehensive answer.
        3. Relevance: Ensure the answer directly addresses the original query.
        4. Accuracy: Cross-reference information across sources to ensure factual correctness.
        5. Completeness: Cover all major aspects of the query in your answer.
        6. Clarity: Present the information in a clear, logical, and easy-to-understand manner.
        7. Objectivity: Maintain a neutral tone and present different viewpoints if applicable.
        8. Currency: Emphasize the most recent developments or information when relevant.
        9. References: Properly cite sources used in formulating the answer.

        Your output must be a JSON object with the following fields:
        1. 'original_query': The exact original query string.
        2. 'answer': A detailed, well-structured answer to the query, typically 2-3 paragraphs long.
        3. 'references': A list of dictionaries, each containing 'title' and 'url' of the sources used.

        Example output format:
        {
            "original_query": "What are the latest developments in quantum computing?",
            "answer": "Recent developments in quantum computing have been marked by significant breakthroughs in both theoretical and practical domains. One of the most notable advancements is in error correction techniques, crucial for maintaining quantum coherence. Researchers at Company X have developed a new quantum error correction code that can protect quantum information for substantially longer periods, potentially bringing us closer to practical quantum computers.

            Another major milestone is the demonstration of quantum supremacy by Company Y. Their 54-qubit processor completed a specific task in 200 seconds that would take the most powerful classical supercomputer approximately 10,000 years. This achievement, while still for a narrow application, represents a significant step towards proving the practical advantages of quantum computing.

            In the realm of applications, quantum algorithms are showing promise in drug discovery. Research Institute Z has successfully used a quantum simulator to model complex molecular interactions, potentially accelerating the process of identifying new therapeutic compounds. While these developments are exciting, it's important to note that many challenges remain, particularly in scaling up quantum systems and making them more robust for practical, real-world applications.",
            "references": [
                {
                    "title": "Breakthrough in Quantum Error Correction",
                    "url": "https://company-x.com/quantum-error-correction"
                },
                {
                    "title": "Quantum Supremacy Achieved",
                    "url": "https://company-y.com/quantum-supremacy-paper"
                },
                {
                    "title": "Quantum Computing in Drug Discovery",
                    "url": "https://institute-z.org/quantum-drug-discovery"
                }
            ]
        }

        Analyze the following aggregated search results and formulate a final answer:
        """

        final_answer = create_bedrock_structured_output(
            pydantic_model=FinalAnswer,
            model_id=SMART_LLM,
            temperature=0.7,
            system_prompt=system_prompt,
            region_name=AWS_REGION,
        )
        return final_answer.invoke(aggregated_results.dict())
    except ClientError as e:
        logger.error(f"Error formulating final answer: {e}")
        return FinalAnswer(
            original_query=aggregated_results.original_query,
            answer="We apologize, but an error occurred while formulating the final answer. This could be due to a temporary system issue or complexity in processing the search results. Please try your query again or rephrase it for a new search.",
            references=[],
        )
