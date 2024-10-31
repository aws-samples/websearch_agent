from typing import Tuple, Optional
from exceptions import ConfigurationError
from utils import logger

def validate_search_params(
    action_group: str,
    function: str,
    parameters: list,
    valid_action_group: str,
    valid_functions: list
) -> Tuple[str, Optional[str]]:
    if action_group != valid_action_group:
        raise ConfigurationError(f"Invalid action group: {action_group}")
        
    if function not in valid_functions:
        raise ConfigurationError(f"Invalid function: {function}")
        
    search_query = next(
        (param["value"] for param in parameters if param["name"] == "search_query"),
        None,
    )
    if not search_query:
        raise ConfigurationError("Missing required parameter: search_query")

    target_website = next(
        (param["value"] for param in parameters if param["name"] == "target_website"),
        None,
    )
    
    logger.debug(f"validate_search_params: {search_query=} {target_website=}")
    return search_query, target_website
