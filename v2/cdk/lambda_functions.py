import aws_cdk.aws_iam as iam
from aws_cdk import Duration, BundlingOptions
from aws_cdk import aws_lambda as _lambda
from constructs import Construct
from .websearch_lambda_layers import WebSearchLambdaLayers


def create_lambda_functions(
    self: Construct,
    construct_id: str,
    websearch_lambda_role: iam.Role,
    advanced_web_search_lambda_role: iam.Role,
    lambda_layers: WebSearchLambdaLayers,
    config: dict,
) -> tuple[_lambda.Function, _lambda.Function]:
    websearch_lambda = _lambda.Function(
        self,
        "WebSearch",
        function_name=config["WEBSEARCH_FUNCTION_NAME"],
        runtime=_lambda.Runtime.PYTHON_3_12,
        architecture=_lambda.Architecture.ARM_64,
        code=_lambda.Code.from_asset("lambda/websearch"),
        layers=[
            lambda_layers.project_dependencies,
            lambda_layers.aws_lambda_powertools,
        ],
        handler="websearch_lambda.lambda_handler",
        timeout=Duration.seconds(300),
        role=websearch_lambda_role,
        environment={
            "LOG_LEVEL": "DEBUG",
            "ACTION_GROUP": f"{config['WEBSEARCH_ACTION_GROUP_NAME']}",
        },
    )

    advanced_web_search_lambda = _lambda.Function(
        self,
        "AdvancedWebSearch",
        function_name=config["ADVANCED_SEARCH_FUNCTION_NAME"],
        runtime=_lambda.Runtime.PYTHON_3_12,
        architecture=_lambda.Architecture.ARM_64,
        code=_lambda.Code.from_asset("lambda/advanced_web_search"),
        layers=[
            lambda_layers.project_dependencies,
            lambda_layers.aws_lambda_powertools,
        ],
        handler="advanced_web_search_lambda.lambda_handler",
        timeout=Duration.seconds(300),
        role=advanced_web_search_lambda_role,
        environment={
            "LOG_LEVEL": "DEBUG",
            "ACTION_GROUP": f"{config['ADVANCED_SEARCH_ACTION_GROUP_NAME']}",
            "SMART_LLM": config["SMART_LLM"],
            "FAST_LLM": config["FAST_LLM"],
            "CROSS_REGION_INFERENCE": config["use_cross_region_inference"],
        },
    )

    return websearch_lambda, advanced_web_search_lambda


def create_lambda_roles(
    self: Construct,
    construct_id: str,
    lambda_policy: iam.Policy,
    config: dict,
) -> tuple[iam.Role, iam.Role]:
    websearch_lambda_role = iam.Role(
        self,
        "WebSearchLambdaRole",
        role_name=f"{config['WEBSEARCH_FUNCTION_NAME']}_role",
        assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
    )
    websearch_lambda_role.attach_inline_policy(lambda_policy)

    advanced_web_search_lambda_role = iam.Role(
        self,
        "AdvancedWebSearchLambdaRole",
        role_name=f"{config['ADVANCED_SEARCH_FUNCTION_NAME']}_role",
        assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
    )
    advanced_web_search_lambda_role.attach_inline_policy(lambda_policy)

    cross_region_prefix = config["DEPLOY_REGION"][:2] + "."

    # Add Bedrock model invocation permissions to both Lambda roles
    bedrock_policy = iam.PolicyStatement(
        sid="AmazonBedrockInvokeModelPolicy",
        effect=iam.Effect.ALLOW,
        actions=[
            "bedrock:InvokeModel",
            "bedrock:Converse",
        ],
        resources=[
            f"arn:aws:bedrock:{config['DEPLOY_REGION']}::foundation-model/{config['SMART_LLM']}",
            f"arn:aws:bedrock:{config['DEPLOY_REGION']}::foundation-model/{config['FAST_LLM']}",
            f"arn:aws:bedrock:{config['DEPLOY_REGION']}::foundation-model/{cross_region_prefix}{config['SMART_LLM']}",
            f"arn:aws:bedrock:{config['DEPLOY_REGION']}::foundation-model/{cross_region_prefix}{config['FAST_LLM']}",
        ],
    )
    websearch_lambda_role.add_to_policy(bedrock_policy)
    advanced_web_search_lambda_role.add_to_policy(bedrock_policy)

    return websearch_lambda_role, advanced_web_search_lambda_role
