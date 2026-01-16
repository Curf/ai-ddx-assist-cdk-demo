#!/usr/bin/env python3
import os

import aws_cdk as cdk

from medical_imaging_cdk.medical_imaging_stack import MedicalImagingStack


app = cdk.App()

# Get environment from context or environment variable (defaults to 'dev')
environment = app.node.try_get_context("environment") or os.getenv("CDK_ENVIRONMENT", "dev")

# Get account and region from context, environment variables, or CLI defaults
target_account = (
    app.node.try_get_context("account") 
    or os.getenv("CDK_DEFAULT_ACCOUNT")
    or os.getenv("CDK_ACCOUNT")
)
target_region = (
    app.node.try_get_context("region")
    or os.getenv("CDK_DEFAULT_REGION")
    or os.getenv("CDK_REGION", "us-east-1")
)

# Create environment configuration
env_config = None
if target_account:
    env_config = cdk.Environment(
        account=target_account,
        region=target_region
    )

# Create stack with environment-specific name
stack_name = f"MedicalImagingStack-{environment}"
MedicalImagingStack(
    app,
    stack_name,
    env=env_config,
    environment=environment,
)

app.synth()
