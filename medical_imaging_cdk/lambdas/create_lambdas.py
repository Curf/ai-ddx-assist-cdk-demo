from aws_cdk import (
    aws_lambda as lambda_,
    Duration,
    aws_iam as iam,
)
from constructs import Construct

def create_metadata_extractor(scope: Construct, layers: dict, role: iam.IRole) -> lambda_.Function:
    """Creates a Lambda function for extracting metadata from medical images."""
    metadata_extractor = lambda_.Function(
        scope, "MetadataExtractor",
        function_name="MetadataExtractor",
        role=role,
        runtime=lambda_.Runtime.NODEJS_20_X,
        handler="src/index.handler",
        code=lambda_.Code.from_asset(
            "medical_imaging_cdk/lambdas/MetadataExtractor",
            exclude=[
                "**",  # Exclude everything
                "!src",  # Include src folder
                "!src/**"  # Include all contents of src folder
            ]
        ),
        timeout=Duration.seconds(30),
        memory_size=128,
        layers=[layers["axios_layer"], layers["langfuse_layer"]],
        architecture=lambda_.Architecture.ARM_64,
    )
    return metadata_extractor

def create_image_processor(scope: Construct, layers: dict, role: iam.IRole) -> lambda_.Function:
    """Creates a Lambda function for processing medical images."""
    image_processor = lambda_.Function(
        scope, "ImageProcessor",
        function_name="ImageProcessor",
        role=role,
        runtime=lambda_.Runtime.NODEJS_20_X,
        handler="src/index.handler",
        code=lambda_.Code.from_asset(
            "medical_imaging_cdk/lambdas/ImageProcessor",
            exclude=[
                "**",  # Exclude everything
                "!src",  # Include src folder
                "!src/**"  # Include all contents of src folder
            ]
        ),
        timeout=Duration.seconds(30),
        memory_size=256,
        layers=[layers["axios_layer"], layers["langfuse_layer"]],
        architecture=lambda_.Architecture.ARM_64,
    )
    return image_processor

def create_ai_analyzer(scope: Construct, layers: dict, role: iam.IRole) -> lambda_.Function:
    """Creates a Lambda function for AI analysis of medical images."""
    ai_analyzer = lambda_.Function(
        scope, "AiAnalyzer",
        function_name="AiAnalyzer",
        role=role,
        runtime=lambda_.Runtime.NODEJS_20_X,
        handler="src/index.handler",
        code=lambda_.Code.from_asset(
            "medical_imaging_cdk/lambdas/AiAnalyzer",
            exclude=[
                "**",  # Exclude everything
                "!src",  # Include src folder
                "!src/**"  # Include all contents of src folder
            ]
        ),
        timeout=Duration.seconds(60),  # Increased from 30s for longer AI operations
        memory_size=1024,  # Increased for AI model requirements
        layers=[layers["axios_layer"], layers["langfuse_layer"]],
        architecture=lambda_.Architecture.ARM_64,
    )
    return ai_analyzer

def create_report_generator(scope: Construct, layers: dict, role: iam.IRole) -> lambda_.Function:
    """Creates a Lambda function for generating clinical reports based on AI analysis."""
    report_generator = lambda_.Function(
        scope, "ReportGenerator",
        function_name="ReportGenerator",
        role=role,
        runtime=lambda_.Runtime.NODEJS_20_X,
        handler="src/index.handler",
        code=lambda_.Code.from_asset(
            "medical_imaging_cdk/lambdas/ReportGenerator",
            exclude=[
                "**",  # Exclude everything
                "!src",  # Include src folder
                "!src/**"  # Include all contents of src folder
            ]
        ),
        timeout=Duration.seconds(30),
        memory_size=256,
        layers=[layers["axios_layer"], layers["langfuse_layer"]],
        architecture=lambda_.Architecture.ARM_64,
    )
    return report_generator
