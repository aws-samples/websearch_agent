#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import aws_cdk as cdk
import cdk_nag

from cdk.cdk_stack import WebSearchAgentStack

app = cdk.App()
WebSearchAgentStack(app, "WebSearchAgentStack")

cdk.Aspects.of(app).add(cdk_nag.AwsSolutionsChecks(verbose=True))
app.synth()
