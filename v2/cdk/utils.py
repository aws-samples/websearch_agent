import yaml
from aws_cdk import Aws


def load_config(file_path: str = "config.yaml") -> dict:
    with open(file_path, "r") as config_file:
        config = yaml.safe_load(config_file)

    DEPLOY_REGION = config.get("DEPLOY_REGION", "us-west-2")
    use_cross_region_inference = config.get("USE_CROSS_REGION_INFERENCE", "True")
    if use_cross_region_inference == True:
        prefix = DEPLOY_REGION[:2]
        SMART_LLM = (
            prefix
            + "."
            + config.get("SMART_LLM", "anthropic.claude-3-5-sonnet-20240620-v1:0")
        )
        FAST_LLM = (
            prefix
            + "."
            + config.get("FAST_LLM", "anthropic.claude-3-haiku-20240307-v1:0")
        )
    else:
        SMART_LLM = config.get("SMART_LLM", "anthropic.claude-3-5-sonnet-20240620-v1:0")
        FAST_LLM = config.get("FAST_LLM", "anthropic.claude-3-haiku-20240307-v1:0")

    config.update(
        {
            "DEPLOY_REGION": DEPLOY_REGION,
            "SMART_LLM": SMART_LLM,
            "FAST_LLM": FAST_LLM,
            "use_cross_region_inference": use_cross_region_inference,
        }
    )

    return config


def get_account_id() -> str:
    return Aws.ACCOUNT_ID
