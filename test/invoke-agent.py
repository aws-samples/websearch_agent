# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""

Convenience python script to test agent.
Example use:
  python invoke-agent.py --agent_id RRSS0TTN3H --agent_alias_id 1PSAF8M2LF --prompt "What are the latest AWS news?"

"""

import argparse
import os
import random
import string

try:
    import boto3
except ImportError:
    print("Error: The boto3 library is required. Please install e.g. with 'pip install boto3'")
    os._exit(0)
import botocore

REGION = os.environ["AWS_REGION"]

session = boto3.session.Session()
agents_runtime_client = session.client(service_name="bedrock-agent-runtime", region_name=REGION)


def invoke_agent(agent_id, agent_alias_id, session_id, prompt):
    """
    Sends a prompt for the agent to process and respond to.

    :param agent_id: The unique identifier of the agent to use.
    :param agent_alias_id: The alias of the agent to use.
    :param session_id: The unique identifier of the session. Use the same value across requests
                       to continue the same conversation.
    :param prompt: The prompt that you want Claude to complete.
    :return: Inference response from the model.
    """

    try:
        # Note: The execution time depends on the foundation model, complexity of the agent, and
        # the length of the prompt. In some cases, it can take up to a minute or more to generate a response.
        response = agents_runtime_client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=prompt,
        )

        completion = ""
        for event in response.get("completion"):
            chunk = event["chunk"]
            completion = completion + chunk["bytes"].decode()

    except botocore.exceptions.ClientError as e:
        print(f"Couldn't invoke agent. {e}")
        raise

    return completion


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent_id", required=True, help="The unique identifier of the agent to use.")
    parser.add_argument("--agent_alias_id", required=True, help="The alias of the agent to use.")
    parser.add_argument("--prompt", required=True, help="The prompt that you want Claude to complete.")
    args = parser.parse_args()

    session_id = "".join(random.choices(string.ascii_lowercase, k=10))  # nosec B311 no cryptographic purpose use

    response = invoke_agent(args.agent_id, args.agent_alias_id, session_id, args.prompt)

    print(response)
