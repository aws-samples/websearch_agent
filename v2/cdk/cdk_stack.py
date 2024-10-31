# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from typing import Any, Self

import aws_cdk.aws_iam as iam
import cdk_nag
from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_lambda as _lambda
from constructs import Construct
from .websearch_lambda_layers import WebSearchLambdaLayers

from .bedrock_agent import create_bedrock_agent
from .lambda_functions import create_lambda_functions, create_lambda_roles
from .log_groups import create_log_groups
from .utils import load_config, get_account_id


class WebSearchAgentStack(Stack):
    def __init__(
        self: Self, scope: Construct, construct_id: str, **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Load configuration
        config = load_config()

        # Create Lambda layers
        lambda_layers = WebSearchLambdaLayers(
            self,
            "WebSearchLambdaLayers",
            stack_name=construct_id,
            architecture=_lambda.Architecture.ARM_64,
            region=config['DEPLOY_REGION']
        )

        # Create log groups
        websearch_log_group, advanced_web_search_log_group = create_log_groups(
            self, construct_id, config
        )

        lambda_policy = iam.Policy(
            self,
            "LambdaPolicy",
            statements=[
                iam.PolicyStatement(
                    sid="CreateLogGroup",
                    effect=iam.Effect.ALLOW,
                    actions=["logs:CreateLogGroup"],
                    resources=[
                        f"arn:aws:logs:{config['DEPLOY_REGION']}:{get_account_id()}:*"
                    ],
                ),
                iam.PolicyStatement(
                    sid="CreateLogStreamAndPutLogEvents",
                    effect=iam.Effect.ALLOW,
                    actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                    resources=[
                        websearch_log_group.log_group_arn,
                        f"{websearch_log_group.log_group_arn}:log-stream:*",
                        advanced_web_search_log_group.log_group_arn,
                        f"{advanced_web_search_log_group.log_group_arn}:log-stream:*",
                    ],
                ),
                iam.PolicyStatement(
                    sid="GetSecretsManagerSecret",
                    effect=iam.Effect.ALLOW,
                    actions=["secretsmanager:GetSecretValue"],
                    resources=[
                        f"arn:aws:secretsmanager:{config['DEPLOY_REGION']}:{get_account_id()}:secret:SERPER_API_KEY-*",
                        f"arn:aws:secretsmanager:{config['DEPLOY_REGION']}:{get_account_id()}:secret:TAVILY_API_KEY-*",
                    ],
                ),
            ],
        )
        cdk_nag.NagSuppressions.add_resource_suppressions(
            lambda_policy,
            [
                cdk_nag.NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="'log-stream:*' - stream names dynamically generated at runtime",
                )
            ],
        )

        # Create Lambda roles
        websearch_lambda_role, advanced_web_search_lambda_role = create_lambda_roles(
            self, construct_id, lambda_policy, config
        )

        # Add suppressions for Lambda roles
        cdk_nag.NagSuppressions.add_resource_suppressions(
            websearch_lambda_role,
            [
                cdk_nag.NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Lambda role requires access to CloudWatch logs and Secrets Manager",
                    applies_to=[
                        "Resource::arn:aws:logs:<REGION>:<ACCOUNT>:log-group:/aws/lambda/*:*",
                        "Resource::arn:aws:secretsmanager:<REGION>:<ACCOUNT>:secret:SERPER_API_KEY-*",
                        "Resource::arn:aws:secretsmanager:<REGION>:<ACCOUNT>:secret:TAVILY_API_KEY-*",
                    ],
                )
            ],
        )
        cdk_nag.NagSuppressions.add_resource_suppressions(
            advanced_web_search_lambda_role,
            [
                cdk_nag.NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Lambda role requires access to CloudWatch logs and Secrets Manager",
                    applies_to=[
                        "Resource::arn:aws:logs:<REGION>:<ACCOUNT>:log-group:/aws/lambda/*:*",
                        "Resource::arn:aws:secretsmanager:<REGION>:<ACCOUNT>:secret:SERPER_API_KEY-*",
                        "Resource::arn:aws:secretsmanager:<REGION>:<ACCOUNT>:secret:TAVILY_API_KEY-*",
                    ],
                )
            ],
        )

        # Create Lambda functions
        websearch_lambda, advanced_web_search_lambda = create_lambda_functions(
            self,
            construct_id,
            websearch_lambda_role,
            advanced_web_search_lambda_role,
            lambda_layers,
            config,
        )

        bedrock_account_principal = iam.PrincipalWithConditions(
            iam.ServicePrincipal("bedrock.amazonaws.com"),
            conditions={
                "StringEquals": {"aws:SourceAccount": f"{get_account_id()}"},
            },
        )
        websearch_lambda.add_permission(
            id="WebSearchLambdaResourcePolicyAgentsInvokeFunction",
            principal=bedrock_account_principal,
            action="lambda:invokeFunction",
        )
        advanced_web_search_lambda.add_permission(
            id="AdvancedWebSearchLambdaResourcePolicyAgentsInvokeFunction",
            principal=bedrock_account_principal,
            action="lambda:invokeFunction",
        )

        agent_policy = iam.Policy(
            self,
            "AgentPolicy",
            statements=[
                iam.PolicyStatement(
                    sid="AmazonBedrockAgentBedrockFoundationModelPolicy",
                    effect=iam.Effect.ALLOW,
                    actions=["bedrock:InvokeModel"],
                    resources=[
                        f"arn:aws:bedrock:{config['DEPLOY_REGION']}::foundation-model/{config['SMART_LLM']}",
                        f"arn:aws:bedrock:{config['DEPLOY_REGION']}::foundation-model/{config['FAST_LLM']}",
                    ],
                ),
            ],
        )

        # Add suppression for agent policy
        cdk_nag.NagSuppressions.add_resource_suppressions(
            agent_policy,
            [
                cdk_nag.NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Agent policy requires access to Bedrock foundation models",
                    applies_to=[
                        f"Resource::arn:aws:bedrock:{config['DEPLOY_REGION']}::foundation-model/{config['SMART_LLM']}",
                        f"Resource::arn:aws:bedrock:{config['DEPLOY_REGION']}::foundation-model/{config['FAST_LLM']}",
                    ],
                )
            ],
        )

        agent_role_trust = iam.PrincipalWithConditions(
            iam.ServicePrincipal("bedrock.amazonaws.com"),
            conditions={
                "StringLike": {"aws:SourceAccount": f"{get_account_id()}"},
                "ArnLike": {
                    "aws:SourceArn": f"arn:aws:bedrock:{config['DEPLOY_REGION']}:{get_account_id()}:agent/*"
                },
            },
        )
        agent_role = iam.Role(
            self,
            "AmazonBedrockExecutionRoleForAgents",
            role_name=f"AmazonBedrockExecutionRoleForAgents_{config['AGENT_NAME']}",
            assumed_by=agent_role_trust,
        )
        agent_role.attach_inline_policy(agent_policy)

        # Create Bedrock agent
        agent, agent_alias = create_bedrock_agent(
            self,
            construct_id,
            websearch_lambda,
            advanced_web_search_lambda,
            agent_role,
            config,
        )

        CfnOutput(self, "agent_id", value=agent.attr_agent_id)
        CfnOutput(self, "agent_alias_id", value=agent_alias.attr_agent_alias_id)
        CfnOutput(self, "agent_version", value=agent.attr_agent_version)
