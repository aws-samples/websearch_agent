import os

AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")
ACTION_GROUP_NAME = os.environ.get("ACTION_GROUP", "action-group-web-search-d213q")
FUNCTION_NAMES = ["tavily-ai-search", "google-search"]
