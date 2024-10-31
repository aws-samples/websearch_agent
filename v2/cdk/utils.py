import yaml
from aws_cdk import Aws
import uuid


def generate_resource_suffix():
    """Generate a short UUID suffix for resource names"""
    return uuid.uuid4().hex[:4]


def load_config(file_path: str = "config.yaml") -> dict:
    with open(file_path, "r") as config_file:
        config = yaml.safe_load(config_file)

    # Handle region and cross-region inference first
    DEPLOY_REGION = config.get("DEPLOY_REGION", "us-west-2")
    use_cross_region_inference = config.get("CROSS_REGION_INFERENCE", True)
    
    # Handle model names based on cross-region inference
    if use_cross_region_inference:
        prefix = DEPLOY_REGION[:2]
        SMART_LLM = f"{prefix}.{config.get('SMART_LLM')}"
        FAST_LLM = f"{prefix}.{config.get('FAST_LLM')}"
    else:
        SMART_LLM = config.get("SMART_LLM")
        FAST_LLM = config.get("FAST_LLM")

    # Generate UUID suffix if enabled
    if config.get("ADD_UUID_NAMING", False):
        suffix = generate_resource_suffix()
        # Add suffix to resource names
        config["WEBSEARCH_FUNCTION_NAME"] = f"{config['WEBSEARCH_FUNCTION_NAME']}_{suffix}"
        config["ADVANCED_SEARCH_FUNCTION_NAME"] = f"{config['ADVANCED_SEARCH_FUNCTION_NAME']}_{suffix}"
        config["AGENT_NAME"] = f"{config['AGENT_NAME']}_{suffix}"
        config["WEBSEARCH_ACTION_GROUP_NAME"] = f"{config['WEBSEARCH_ACTION_GROUP_NAME']}_{suffix}"
        config["ADVANCED_SEARCH_ACTION_GROUP_NAME"] = f"{config['ADVANCED_SEARCH_ACTION_GROUP_NAME']}_{suffix}"

    config.update({
        "DEPLOY_REGION": DEPLOY_REGION,
        "SMART_LLM": SMART_LLM,
        "FAST_LLM": FAST_LLM,
        "use_cross_region_inference": use_cross_region_inference,
    })

    return config


def get_account_id() -> str:
    return Aws.ACCOUNT_ID
