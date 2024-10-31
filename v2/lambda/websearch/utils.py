import logging
import os
import boto3
from typing import Optional

def setup_logging() -> logging.Logger:
    """Configure and return a logger with proper formatting"""
    log_level = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
    logging.basicConfig(
        format="[%(asctime)s] p%(process)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    return logger

def is_env_var_set(env_var: str) -> bool:
    """Check if environment variable is set and truthy"""
    return env_var in os.environ and os.environ[env_var] not in (
        "",
        "0",
        "false",
        "False",
    )

def get_from_secretstore_or_env(key: str, region: str) -> str:
    """Get value from Secrets Manager or environment variable"""
    if is_env_var_set(key):
        logger.warning(
            f"Getting value for {key} from environment var; recommended to use AWS Secrets Manager instead"
        )
        return os.environ[key]

    session = boto3.session.Session()
    secrets_manager = session.client(
        service_name="secretsmanager", region_name=region
    )
    try:
        secret_value = secrets_manager.get_secret_value(SecretId=key)
    except Exception as e:
        logger.error(f"Could not get secret {key} from secrets manager: {e}")
        raise e

    return secret_value["SecretString"]

logger = setup_logging()
