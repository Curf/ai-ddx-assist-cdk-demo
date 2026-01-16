from aws_cdk import (
    aws_lambda as lambda_,
)
from constructs import Construct


def create_layers(scope: Construct) -> dict:
    """
    Create and return Lambda layers used in the medical imaging analysis system.
    """
    # Layer for axios HTTP client
    axios_layer = lambda_.LayerVersion(
        scope,
        "AxiosLayer",
        code=lambda_.Code.from_asset("medical_imaging_cdk/layers/axios-layer"),
        compatible_runtimes=[lambda_.Runtime.NODEJS_20_X],
        description="Layer containing axios for HTTP requests",
    )

    # Layer for Langfuse for LLM tracking and prompt management
    langfuse_layer = lambda_.LayerVersion(
        scope,
        "LangfuseLayer",
        code=lambda_.Code.from_asset("medical_imaging_cdk/layers/langfuse-layer"),
        compatible_runtimes=[lambda_.Runtime.NODEJS_20_X],
        description="Layer containing Langfuse for LLM observability",
    )

    # Return all layers in a dictionary for easy access
    return {
        "axios_layer": axios_layer,
        "langfuse_layer": langfuse_layer,
    }
