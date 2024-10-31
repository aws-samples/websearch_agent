from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class SearchParameters(BaseModel):
    name: str
    value: str

class SearchEvent(BaseModel):
    actionGroup: str
    function: str
    parameters: List[SearchParameters]
    messageVersion: str

class SearchResponse(BaseModel):
    response: Dict[str, Any]
    messageVersion: str
