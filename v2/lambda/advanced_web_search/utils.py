import json
import logging
import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def is_env_var_set(env_var: str) -> bool:
    """
    Check if an environment variable exists and has a non-empty/non-false value.

    Args:
        env_var (str): The name of the environment variable to check

    Returns:
        bool: True if the environment variable exists and has a value other than
            empty string, "0", "false", or "False". False otherwise.
    """
    return env_var in os.environ and os.environ[env_var] not in (
        "",
        "0",
        "false",
        "False",
    )


def get_from_secretstore_or_env(key: str, region: Optional[str]) -> str:
    """
    Retrieve a secret value either from environment variables or AWS Secrets Manager.

    First checks if the value exists as an environment variable. If it does, returns
    that value with a warning. If not, attempts to retrieve the value from AWS
    Secrets Manager in the specified region.

    Args:
        key (str): The key/name of the secret to retrieve
        region (Optional[str]): AWS region for Secrets Manager. If None, uses AWS_REGION
            environment variable

    Returns:
        str: The secret value

    Raises:
        Exception: If the secret cannot be retrieved from AWS Secrets Manager
    """
    if is_env_var_set(key):
        logger.warning(
            f"getting value for {key} from environment var; recommended to use AWS Secrets Manager instead"
        )
        return os.environ[key]

    session = boto3.session.Session()
    secrets_manager = session.client(
        service_name="secretsmanager",
        region_name=region if region else os.getenv("AWS_REGION"),
    )
    logger.info(f"getting secret {key} from AWS Secrets Manager in region {region}.")
    try:
        secret_value = secrets_manager.get_secret_value(SecretId=key)
    except Exception as e:
        logger.error(f"could not get secret {key} from secrets manager: {e}")
        raise e

    secret: str = secret_value["SecretString"]

    return secret
