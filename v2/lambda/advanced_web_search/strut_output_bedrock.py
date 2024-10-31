import json
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel, ValidationError
from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage, HumanMessage
import boto3
import os
import json


class MaxTokensReachedException(Exception):
    pass


class BedrockStructuredOutput(Runnable):

    def __init__(
        self,
        pydantic_model: Type[BaseModel],
        model_id: str = "anthropic.claude-3-haiku-20240307-v1:0",
        temperature: float = 0.0,
        max_tokens: Optional[int] = 4096,
        top_p: float = 1.0,
        region_name: str = "us-west-2",  # os.getenv("AWS_REGION"), # TODO: CHange this back to normal region
        system_prompt: str = "",
        include_raw: bool = False,
        bedrock_client: Optional[boto3.client] = None,
    ):
        self.pydantic_model = pydantic_model
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = 4096 if max_tokens is None else max_tokens  # Set default here
        self.top_p = top_p
        self.region_name = region_name
        self.system_prompt = system_prompt
        self.include_raw = include_raw
        self.tool_config = self._create_tool_config()
        self.bedrock_client = (
            bedrock_client
            if bedrock_client is not None
            else boto3.client("bedrock-runtime", region_name="us-west-2")
        )

    def _create_tool_config(self) -> Dict:
        json_schema = self.pydantic_model.model_json_schema()
        return {
            "tools": [
                {
                    "toolSpec": {
                        "name": "structured_output",
                        "description": "Generate structured output",
                        "inputSchema": {"json": json_schema},
                    }
                }
            ],
            "toolChoice": {"tool": {"name": "structured_output"}},
        }

    def _prepare_message(self, inputs: Any) -> List[Dict[str, Any]]:
        return [{"role": "user", "content": [{"text": str(inputs)}]}]

    def _prepare_system_message(self) -> List[Dict[str, Any]]:
        if self.system_prompt:
            return [{"text": self.system_prompt}]
        return []

    def invoke(self, inputs: Any, config: Optional[Dict[str, Any]] = None) -> Any:
        messages = self._prepare_message(inputs)
        system = self._prepare_system_message()

        response = self.bedrock_client.converse(
            modelId=self.model_id,
            messages=messages,
            system=system,
            inferenceConfig={
                "temperature": self.temperature,
                "maxTokens": self.max_tokens,
                "topP": self.top_p,
            },
            toolConfig=self.tool_config,
        )

        if self.include_raw:
            return self._structure_output(response)
        else:
            return self._parse_response(response)

    def _structure_output(self, response: Dict) -> Dict[str, Any]:
        """
        Structures the model response into a dictionary containing both raw and parsed outputs.

        Args:
            response (Dict): The raw response dictionary from the Bedrock model

        Returns:
            Dict[str, Any]: A dictionary containing:
                - raw (AIMessage): The raw model response structured as an AIMessage
                - parsed (Optional[BaseModel]): The response parsed into the configured Pydantic model,
                  or None if parsing failed
                - parsing_error (Optional[str]): Error message if parsing failed, None otherwise

        Notes:
            - Attempts to create both raw and parsed versions of the model output
            - If parsing fails, the parsed output will be None and the error will be captured
            - Raw output is always included regardless of parsing success
        """
        raw_output = self._create_raw_output(response)
        try:
            parsed_output = self._parse_response(response)
            parsing_error = None
        except Exception as e:
            parsed_output = None
            parsing_error = str(e)

        return {
            "raw": raw_output,
            "parsed": parsed_output,
            "parsing_error": parsing_error,
        }

    def _create_raw_output(self, response: Dict) -> AIMessage:
        """
        Creates a structured AIMessage from the raw Bedrock model response.

        Args:
            response (Dict): The raw response dictionary from the Bedrock model containing:
                - output.message.content: List of content items
                - usage: Token usage statistics
                - stopReason: Reason for response completion
                - modelId: ID of the model used
                - id: Response identifier

        Returns:
            AIMessage: A message object containing:
                - content: Empty string
                - additional_kwargs: Dictionary with stop_reason and model_id
                - id: Response identifier
                - tool_calls: List containing extracted tool call information
                - usage_metadata: Dictionary with token usage statistics:
                    - input_tokens: Number of prompt tokens
                    - output_tokens: Number of completion tokens
                    - total_tokens: Total tokens used
        """
        output_message = response.get("output", {}).get("message", {})
        content = output_message.get("content", [])
        usage = response.get("usage", {})
        stop_reason = response.get("stopReason")
        model_id = response.get("modelId")

        return AIMessage(
            content="",
            additional_kwargs={
                "stop_reason": stop_reason,
                "model_id": model_id,
            },
            id=response.get("id", ""),
            tool_calls=[self._extract_tool_call(content)],
            usage_metadata={
                "input_tokens": usage.get("promptTokens", 0),
                "output_tokens": usage.get("completionTokens", 0),
                "total_tokens": usage.get("totalTokens", 0),
            },
        )

    def _extract_tool_call(self, content: List[Dict]) -> Dict:
        """
        Extracts tool call information from the model response content.

        Args:
            content (List[Dict]): The content section of the model response containing possible tool use data.
        Returns:
            Dict: A dictionary containing the tool call information with the following structure:
                {
                    'name': The name of the tool that was called (str),
                    'args': The input arguments passed to the tool (Dict),
                    'id': The unique identifier of the tool call (str),
                    'type': Always set to 'tool_call' (str)
                }
                Returns an empty dictionary if no tool use is found in the content.
        """
        tool_use = next((c["toolUse"] for c in content if "toolUse" in c), None)
        if tool_use:
            return {
                "name": tool_use.get("name", ""),
                "args": tool_use.get("input", {}),
                "id": tool_use.get("id", ""),
                "type": "tool_call",
            }
        return {}

    def _parse_response(self, response: Dict) -> BaseModel:
        """
        Parses the response from the Bedrock model and converts it to a Pydantic model instance.

        Args:
            response (Dict): The raw response dictionary from the Bedrock model

        Returns:
            BaseModel: An instance of the configured Pydantic model containing the structured output

        Raises:
            MaxTokensReachedException: If the response was truncated due to reaching the max token limit
                and either no structured output was found or the output failed validation
            ValidationError: If the structured output fails Pydantic model validation (when not truncated)
            ValueError: If no structured output is found in a complete (non-truncated) response

        Notes:
            - Checks if response was truncated due to max tokens and prints warning if so
            - Extracts structured output from the tool use section of the response
            - Validates the output against the configured Pydantic model
            - Handles truncation cases by raising MaxTokensReachedException when appropriate
        """
        stop_reason = response.get("stopReason")
        is_truncated = stop_reason == "max_tokens"

        if is_truncated:
            print(
                "WARNING: The response was truncated due to reaching the max token limit."
            )

        output_message = response.get("output", {}).get("message", {})
        content = output_message.get("content", [])

        tool_use = next((c["toolUse"] for c in content if "toolUse" in c), None)
        if tool_use:
            output_dict = tool_use["input"]
            try:
                parsed_output = self.pydantic_model(**output_dict)
                if is_truncated:
                    print("Note: Parsed output may be incomplete due to truncation.")
                return parsed_output
            except ValidationError as e:
                print(f"Validation error: {e}")
                if is_truncated:
                    raise MaxTokensReachedException(
                        "Unable to parse the complete structure due to max tokens limit being reached."
                    )
                else:
                    raise  # Re-raise the original ValidationError if not due to truncation
        else:
            if is_truncated:
                raise MaxTokensReachedException(
                    "Structured output not found in the response due to max tokens limit being reached."
                )
            else:
                raise ValueError("Structured output not found in the response")


def create_bedrock_structured_output(
    pydantic_model: Type[BaseModel],
    model_id: str,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    top_p: float = 1.0,
    region_name: str = "us-east-1",
    system_prompt: str = "",
    include_raw: bool = False,
    bedrock_client: Optional[boto3.client] = None,
) -> BedrockStructuredOutput:
    """
    Creates a BedrockStructuredOutput instance for generating structured responses using Amazon Bedrock.

    Args:
        pydantic_model (Type[BaseModel]): The Pydantic model class that defines the structure of the output.
        model_id (str): The identifier of the Amazon Bedrock model to use.
        temperature (float, optional): Controls randomness in the model's output. Defaults to 0.
        max_tokens (Optional[int], optional): Maximum number of tokens in the response. Defaults to None.
        top_p (float, optional): Controls diversity of model output via nucleus sampling. Defaults to 1.0.
        region_name (str, optional): AWS region for the Bedrock service. Defaults to "us-east-1".
        system_prompt (str, optional): System prompt to guide the model's behavior. Defaults to "".
        include_raw (bool, optional): Whether to include raw response data. Defaults to False.
        bedrock_client (Optional[boto3.client], optional): Pre-configured Bedrock client. Defaults to None.

    Returns:
        BedrockStructuredOutput: An instance of BedrockStructuredOutput configured with the provided parameters.
    """
    if bedrock_client is None:
        bedrock_client = boto3.client("bedrock-runtime", region_name=region_name)

    return BedrockStructuredOutput(
        pydantic_model,
        model_id,
        temperature,
        max_tokens,
        top_p,
        region_name,
        system_prompt,
        include_raw,
        bedrock_client,
    )
