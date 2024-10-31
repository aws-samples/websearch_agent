from aws_cdk import aws_logs as logs
from constructs import Construct


def create_log_groups(
    self: Construct,
    construct_id: str,
    config: dict,
) -> tuple[logs.LogGroup, logs.LogGroup]:
    websearch_log_group = logs.LogGroup(
        self,
        "WebSearchLogGroup",
        log_group_name=f"/aws/lambda/{config['WEBSEARCH_FUNCTION_NAME']}",
        retention=logs.RetentionDays.ONE_WEEK,
    )

    advanced_web_search_log_group = logs.LogGroup(
        self,
        "AdvancedWebSearchLogGroup",
        log_group_name=f"/aws/lambda/{config['ADVANCED_SEARCH_FUNCTION_NAME']}",
        retention=logs.RetentionDays.ONE_WEEK,
    )

    return websearch_log_group, advanced_web_search_log_group
