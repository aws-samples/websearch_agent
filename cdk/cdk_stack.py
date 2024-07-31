# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from typing import Any, Self

import aws_cdk.aws_iam as iam
import cdk_nag
from aws_cdk import Aws, CfnOutput, Duration, Stack
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_lambda as _lambda
from constructs import Construct

MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
FUNCTION_NAME = "websearch_lambda"
AGENT_NAME = "websearch_agent"
ACTION_GROUP_NAME = "action-group-web-search"


class WebSearchAgentStack(Stack):  # type: ignore
    def __init__(self: Self, scope: Construct, construct_id: str, **kwargs: Any) -> None:  # type: ignore
        super().__init__(scope, construct_id, **kwargs)

        lambda_policy = iam.Policy(
            self,
            "LambdaPolicy",
            statements=[
                iam.PolicyStatement(
                    sid="CreateLogGroup",
                    effect=iam.Effect.ALLOW,
                    actions=["logs:CreateLogGroup"],
                    resources=[f"arn:aws:logs:{Aws.REGION}:{Aws.ACCOUNT_ID}:*"],
                ),
                iam.PolicyStatement(
                    sid="CreateLogStreamAndPutLogEvents",
                    effect=iam.Effect.ALLOW,
                    actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                    resources=[
                        f"arn:aws:logs:{Aws.REGION}:{Aws.ACCOUNT_ID}:log-group:/aws/lambda/{FUNCTION_NAME}",
                        f"arn:aws:logs:{Aws.REGION}:{Aws.ACCOUNT_ID}:log-group:/aws/lambda/{FUNCTION_NAME}:log-stream:*",
                    ],
                    #                                                log-group:/aws/lambda/action-group-web-search-2j017:log-stream:
                    # resources=[f"arn:aws:logs:{Aws.REGION}:{Aws.ACCOUNT_ID}:log-group:/aws/lambda/{FUNCTION_NAME}:*"],
                ),
                iam.PolicyStatement(
                    sid="GetSecretsManagerSecret",
                    effect=iam.Effect.ALLOW,
                    actions=["secretsmanager:GetSecretValue"],
                    resources=[
                        f"arn:aws:secretsmanager:{Aws.REGION}:{Aws.ACCOUNT_ID}:secret:SERPER_API_KEY-*",
                        f"arn:aws:secretsmanager:{Aws.REGION}:{Aws.ACCOUNT_ID}:secret:TAVILY_API_KEY-*",
                    ],
                ),
            ],
        )
        cdk_nag.NagSuppressions.add_resource_suppressions(
            lambda_policy,
            [cdk_nag.NagPackSuppression(id="AwsSolutions-IAM5", reason="'log-stream:*' - stream names dynamically generated at runtime")],
        )

        lambda_role = iam.Role(
            self,
            "LambdaRole",
            role_name=f"{FUNCTION_NAME}_role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        lambda_role.attach_inline_policy(lambda_policy)

        lambda_function = _lambda.Function(
            self,
            "WebSearch",
            function_name=FUNCTION_NAME,
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            code=_lambda.Code.from_asset("lambda"),
            handler="websearch_lambda.lambda_handler",
            timeout=Duration.seconds(30),
            role=lambda_role,
            environment={"LOG_LEVEL": "DEBUG", "ACTION_GROUP": f"{ACTION_GROUP_NAME}"},
        )

        bedrock_account_principal = iam.PrincipalWithConditions(
            iam.ServicePrincipal("bedrock.amazonaws.com"),
            conditions={
                "StringEquals": {"aws:SourceAccount": f"{Aws.ACCOUNT_ID}"},
            },
        )
        lambda_function.add_permission(
            id="LambdaResourcePolicyAgentsInvokeFunction",
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
                    resources=[f"arn:aws:bedrock:{Aws.REGION}::foundation-model/{MODEL_ID}"],
                ),
            ],
        )

        agent_role_trust = iam.PrincipalWithConditions(
            iam.ServicePrincipal("bedrock.amazonaws.com"),
            conditions={
                "StringLike": {"aws:SourceAccount": f"{Aws.ACCOUNT_ID}"},
                "ArnLike": {"aws:SourceArn": f"arn:aws:bedrock:{Aws.REGION}:{Aws.ACCOUNT_ID}:agent/*"},
            },
        )
        agent_role = iam.Role(
            self,
            "AmazonBedrockExecutionRoleForAgents",
            role_name=f"AmazonBedrockExecutionRoleForAgents_{AGENT_NAME}",
            assumed_by=agent_role_trust,
        )
        agent_role.attach_inline_policy(agent_policy)

        action_group = bedrock.CfnAgent.AgentActionGroupProperty(
            action_group_name=f"{ACTION_GROUP_NAME}",
            description="Action that will trigger the lambda",
            action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(lambda_=lambda_function.function_arn),
            function_schema=bedrock.CfnAgent.FunctionSchemaProperty(
                functions=[
                    bedrock.CfnAgent.FunctionProperty(
                        name="tavily-ai-search",
                        description="""
                            To retrieve information via the internet
                            or for topics that the LLM does not know about and
                            intense research is needed.
                        """,
                        parameters={
                            "search_query": bedrock.CfnAgent.ParameterDetailProperty(
                                type="string",
                                description="The search query for the Tavily web search.",
                                required=True,
                            )
                        },
                    ),
                    bedrock.CfnAgent.FunctionProperty(
                        name="google-search",
                        description="For targeted news, like 'what are the latest news in Austria' or similar.",
                        parameters={
                            "search_query": bedrock.CfnAgent.ParameterDetailProperty(
                                type="string",
                                description="The search query for the Google web search.",
                                required=True,
                            )
                        },
                    ),
                ]
            ),
        )

        agent_instruction = """
            You are an agent that can handle various tasks as described below:

            1/ Helping users do research and finding up to date information. For up to date information always
               uses web search. Web search has two flavours:

               1a/ Google Search - this is great for looking up up to date information and current events

               2b/ Tavily AI Search - this is used to do deep research on topics your user is interested in.
                   Not good on being used on news as it does not order search results by date.

            2/ Retrieving knowledge from the vast knowledge bases that you are connected to.
        """

        agent = bedrock.CfnAgent(
            self,
            "WebSearchAgent",
            agent_name=f"{AGENT_NAME}",
            foundation_model=f"{MODEL_ID}",
            action_groups=[action_group],
            auto_prepare=True,
            instruction=agent_instruction,
            agent_resource_role_arn=agent_role.role_arn,
        )

        agent_alias = bedrock.CfnAgentAlias(
            self,
            "WebSearchAgentAlias",
            agent_id=agent.attr_agent_id,
            agent_alias_name=f"{AGENT_NAME}",
        )

        CfnOutput(self, "agent_id", value=agent.attr_agent_id)
        CfnOutput(self, "agent_alias_id", value=agent_alias.attr_agent_alias_id)
        CfnOutput(self, "agent_version", value=agent.attr_agent_version)
