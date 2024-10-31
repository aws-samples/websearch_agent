from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from constructs import Construct


def create_bedrock_agent(
    self: Construct,
    construct_id: str,
    websearch_lambda: _lambda.Function,
    advanced_web_search_lambda: _lambda.Function,
    agent_role: iam.Role,
    config: dict,
) -> tuple[bedrock.CfnAgent, bedrock.CfnAgentAlias]:
    websearch_action_group = bedrock.CfnAgent.AgentActionGroupProperty(
        action_group_name=f"{config['WEBSEARCH_ACTION_GROUP_NAME']}",
        description="Action that will trigger the websearch lambda",
        action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
            lambda_=websearch_lambda.function_arn  # pylint: disable=unexpected-keyword-arg
        ),
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
                        ),
                        "target_website": bedrock.CfnAgent.ParameterDetailProperty(
                            type="string",
                            description="Limits the search to a specific website.",
                            required=False,
                        ),
                        "search_depth": bedrock.CfnAgent.ParameterDetailProperty(
                            type="string",
                            description="The depth of the search. Can be 'basic' or 'advanced'. Basic uses 1 credit, advanced uses 2 credits.",
                            required=False,
                        ),
                        "max_results": bedrock.CfnAgent.ParameterDetailProperty(
                            type="integer",
                            description="The maximum number of search results to return. Default is 3.",
                            required=False,
                        ),
                        "topic": bedrock.CfnAgent.ParameterDetailProperty(
                            type="string", 
                            description="Category of search. Supports 'general' or 'news'. Default is 'general'.",
                            required=False,
                        ),
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
                        ),
                        "target_website": bedrock.CfnAgent.ParameterDetailProperty(
                            type="string",
                            description="Limits the search to a specific website.",
                            required=False,
                        ),
                        "search_type": bedrock.CfnAgent.ParameterDetailProperty(
                            type="string",
                            description="Type of search to perform. Options: 'search' (web search), 'news' (news search).",
                            required=False,
                        ),
                        "time_period": bedrock.CfnAgent.ParameterDetailProperty(
                            type="string",
                            description="Filter results by recency. Options: 'qdr:h' (past hour), 'qdr:d' (past day), 'qdr:w' (past week), 'qdr:m' (past month), 'qdr:y' (past year).",
                            required=False,
                        ),
                        "country_code": bedrock.CfnAgent.ParameterDetailProperty(
                            type="string",
                            description="Two-letter country code for localized results.",
                            required=False,
                        ),
                    },
                ),
            ]
        ),
    )

    advanced_web_search_action_group = bedrock.CfnAgent.AgentActionGroupProperty(
        action_group_name=f"{config['ADVANCED_SEARCH_ACTION_GROUP_NAME']}",
        description="Action that will trigger the advanced web search lambda",
        action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
            lambda_=advanced_web_search_lambda.function_arn  # pylint: disable=unexpected-keyword-arg
        ),
        function_schema=bedrock.CfnAgent.FunctionSchemaProperty(
            functions=[
                bedrock.CfnAgent.FunctionProperty(
                    name="advanced-web-search",
                    description="""
                        To perform a comprehensive search with query rewriting,
                        subquery searching, and result checking.
                    """,
                    parameters={
                        "search_query": bedrock.CfnAgent.ParameterDetailProperty(
                            type="string",
                            description="The search query for the Advanced Web Search.",
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
           uses web search. Web search has three flavours:

           1a/ Google Search - this is great for looking up up to date information and current events

           1b/ Tavily AI Search - this is used to do deep research on topics your user is interested in.
               Not good on being used on news as it does not order search results by date.

           1c/ Advanced Web Search - this performs a comprehensive search with query rewriting,
               subquery searching, and result checking. Use this for complex queries that require
               a more thorough analysis.

    """

    agent = bedrock.CfnAgent(
        self,
        "WebSearchAgent",
        agent_name=f"{config['AGENT_NAME']}",
        foundation_model=config["SMART_LLM"],
        action_groups=[websearch_action_group, advanced_web_search_action_group],
        auto_prepare=True,
        instruction=agent_instruction,
        agent_resource_role_arn=agent_role.role_arn,
    )

    agent_alias = bedrock.CfnAgentAlias(
        self,
        "WebSearchAgentAlias",
        agent_id=agent.attr_agent_id,
        agent_alias_name=f"{config['AGENT_NAME']}",
    )

    return agent, agent_alias
