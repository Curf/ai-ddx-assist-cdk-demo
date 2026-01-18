from aws_cdk import (
    aws_lambda as lambda_,
    Duration,
    aws_iam as iam,
)
from constructs import Construct

def create_refresh_creds(scope: Construct, layers: dict, role: iam.IRole) -> lambda_.Function:
    """Creates a Lambda function for refreshing credentials for EHR API access.
    
    Given a firm ID, it looks up the secret and gets a fresh token if expired,
    otherwise passes the token to the state machine.
    """
    refresh_creds = lambda_.Function(
        scope, "RefreshCreds",
        function_name="RefreshCreds",
        role=role,
        runtime=lambda_.Runtime.NODEJS_20_X,
        handler="src/index.handler",
        code=lambda_.Code.from_asset(
            "medical_imaging_cdk/lambdas/RefreshCreds",
            exclude=[
                "**",  # Exclude everything
                "!src",  # Include src folder
                "!src/**"  # Include all contents of src folder
            ]
        ),
        timeout=Duration.seconds(30),
        memory_size=128,
        layers=[layers["axios_layer"], layers["params_layer"]],
        architecture=lambda_.Architecture.ARM_64,
    )
    return refresh_creds

def create_encounter_poller(scope: Construct, layers: dict, role: iam.IRole) -> lambda_.Function:
    """Creates a Lambda function for polling active encounters from EHR API.
    
    Polls 'Encounter' resource for active encounters and posts all new encounters 
    to the EncounterWatch table with a TTL of 24 hours.
    """
    encounter_poller = lambda_.Function(
        scope, "EncounterPoller",
        function_name="Encounter-Poller",
        role=role,
        runtime=lambda_.Runtime.NODEJS_20_X,
        handler="src/index.handler",
        code=lambda_.Code.from_asset(
            "medical_imaging_cdk/lambdas/Encounter-Poller",
            exclude=[
                "**",  # Exclude everything
                "!src",  # Include src folder
                "!src/**"  # Include all contents of src folder
            ]
        ),
        timeout=Duration.seconds(30),
        memory_size=128,
        layers=[layers["axios_layer"], layers["params_layer"]],
        architecture=lambda_.Architecture.ARM_64,
    )
    return encounter_poller

def create_document_poller(scope: Construct, layers: dict, role: iam.IRole) -> lambda_.Function:
    """Creates a Lambda function for polling document resources for encounters in the watch list.
    
    Performs concurrent processing by leasing and polling batches of encounters in the watch list
    for documents with target label category. Saves found docs to DocumentWatch table.
    """
    document_poller = lambda_.Function(
        scope, "DocumentPoller",
        function_name="Document-Poller",
        role=role,
        runtime=lambda_.Runtime.NODEJS_20_X,
        handler="src/index.handler",
        code=lambda_.Code.from_asset(
            "medical_imaging_cdk/lambdas/Document-Poller",
            exclude=[
                "**",  # Exclude everything
                "!src",  # Include src folder
                "!src/**"  # Include all contents of src folder
            ]
        ),
        timeout=Duration.seconds(60),  # Increased timeout for batch operations
        memory_size=512,  # Increased memory for concurrent processing
        layers=[layers["axios_layer"], layers["params_layer"]],
        architecture=lambda_.Architecture.ARM_64,
    )
    return document_poller

def create_download_image(scope: Construct, layers: dict, role: iam.IRole) -> lambda_.Function:
    """Creates a Lambda function for downloading images using pre-signed URLs.
    
    Triggered by inserts to DocumentWatch table. Uses pre-signed URL to download 
    the image and saves it with all metadata to S3.
    """
    download_image = lambda_.Function(
        scope, "DownloadImage",
        function_name="DownloadDdxAssistImage",
        role=role,
        runtime=lambda_.Runtime.NODEJS_20_X,
        handler="src/index.handler",
        code=lambda_.Code.from_asset(
            "medical_imaging_cdk/lambdas/DownloadDdxAssistImage",
            exclude=[
                "**",  # Exclude everything
                "!src",  # Include src folder
                "!src/**"  # Include all contents of src folder
            ]
        ),
        timeout=Duration.seconds(30),
        memory_size=128,
        layers=[layers["axios_layer"]],
        architecture=lambda_.Architecture.ARM_64,
    )
    return download_image

def create_get_ddx_assist_inference(scope: Construct, layers: dict, role: iam.IRole) -> lambda_.Function:
    """Creates a Lambda function for AI analysis of medical images.
    
    Triggered by inserts to target S3 location. Gets the image, passes it through object 
    detection if 'solitary' model version; otherwise passes to classifier SageMaker endpoint. 
    Compiles prompt using classification probabilities and patient context, passes to LLM. 
    Saves LLM's next step recommendations, classification top-5, etc. to AIAssistResults table.
    """
    get_ddx_assist_inference = lambda_.Function(
        scope, "GetDdxAssistInference",
        function_name="GetDdxAssistInference",
        role=role,
        runtime=lambda_.Runtime.NODEJS_20_X,
        handler="src/index.handler",
        code=lambda_.Code.from_asset(
            "medical_imaging_cdk/lambdas/GetDdxAssistInference",
            exclude=[
                "**",  # Exclude everything
                "!src",  # Include src folder
                "!src/**"  # Include all contents of src folder
            ]
        ),
        timeout=Duration.seconds(60),  # Increased for AI processing
        memory_size=1024,  # Increased for AI model requirements
        layers=[layers["axios_layer"], layers["langfuse_layer"]],
        architecture=lambda_.Architecture.ARM_64,
    )
    return get_ddx_assist_inference

def create_create_composition(scope: Construct, layers: dict, role: iam.IRole) -> lambda_.Function:
    """Creates a Lambda function for creating compositions in the EHR system.
    
    Triggered by insert to AIAssistResults table. Constructs/formats composition 
    results and posts back to EHR API for doctors to view.
    """
    create_composition = lambda_.Function(
        scope, "CreateComposition",
        function_name="CreateComposition",
        role=role,
        runtime=lambda_.Runtime.NODEJS_20_X,
        handler="src/index.handler",
        code=lambda_.Code.from_asset(
            "medical_imaging_cdk/lambdas/CreateComposition",
            exclude=[
                "**",  # Exclude everything
                "!src",  # Include src folder
                "!src/**"  # Include all contents of src folder
            ]
        ),
        timeout=Duration.seconds(30),
        memory_size=256,
        layers=[layers["axios_layer"], layers["params_layer"]],
        architecture=lambda_.Architecture.ARM_64,
    )
    return create_composition
