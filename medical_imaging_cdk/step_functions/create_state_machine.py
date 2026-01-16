from aws_cdk import (
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_lambda as lambda_,
    aws_logs as logs,
)
from constructs import Construct


def create_imaging_state_machine(
    scope: Construct,
    metadata_extractor_fn: lambda_.Function,
    image_processor_fn: lambda_.Function,
    ai_analyzer_fn: lambda_.Function,
    log_group: logs.LogGroup,
) -> sfn.StateMachine:
    """
    Create a Step Functions state machine that orchestrates the medical imaging analysis workflow.
    
    Args:
        scope: The CDK construct scope
        metadata_extractor_fn: Lambda function that extracts metadata from incoming images
        image_processor_fn: Lambda function that processes the medical images
        ai_analyzer_fn: Lambda function that performs AI analysis on the processed images
        log_group: CloudWatch log group for state machine execution logs
        
    Returns:
        The created Step Functions state machine
    """
    # Define the Lambda tasks
    extract_metadata_task = tasks.LambdaInvoke(
        scope,
        "ExtractMetadata",
        lambda_function=metadata_extractor_fn,
        payload=sfn.TaskInput.from_object({
            "executionId.$": "$$.Execution.Id",
            "timestamp.$": "$$.State.EnteredTime",
            "input.$": "$"
        }),
        result_path="$.metadataResult",
    )
    
    process_image_task = tasks.LambdaInvoke(
        scope,
        "ProcessImage",
        lambda_function=image_processor_fn,
        payload=sfn.TaskInput.from_object({
            "metadataResult.$": "$.metadataResult.Payload",
            "executionId.$": "$$.Execution.Id",
            "timestamp.$": "$$.State.EnteredTime"
        }),
        result_path="$.processingResult",
    )
    
    analyze_image_task = tasks.LambdaInvoke(
        scope,
        "AnalyzeImage",
        lambda_function=ai_analyzer_fn,
        payload=sfn.TaskInput.from_object({
            "processingResult.$": "$.processingResult.Payload",
            "metadataResult.$": "$.metadataResult.Payload",
            "executionId.$": "$$.Execution.Id",
            "timestamp.$": "$$.State.EnteredTime"
        }),
        result_path="$.analysisResult",
    )
    
    # Define error handler
    handle_error = sfn.Pass(
        scope,
        "HandleError",
        parameters={
            "error.$": "$.error",
            "cause.$": "$.cause",
            "status": "ERROR"
        },
        result_path="$.errorInfo"
    )
    
    # Define retry policies
    standard_retry = sfn.RetryProps(
        max_attempts=3,
        interval=sfn.Duration.seconds(2),
        backoff_rate=2,
        errors=["Lambda.ServiceException", "Lambda.ResourceNotFoundException"],
    )
    
    # Create workflow definition
    workflow_definition = (
        extract_metadata_task
        .add_retry(standard_retry)
        .add_catch(handle_error, result_path="$.error")
        .next(
            process_image_task
            .add_retry(standard_retry)
            .add_catch(handle_error, result_path="$.error")
            .next(
                analyze_image_task
                .add_retry(standard_retry)
                .add_catch(handle_error, result_path="$.error")
            )
        )
    )
    
    # Create state machine
    state_machine = sfn.StateMachine(
        scope,
        "MedicalImagingWorkflow",
        state_machine_name="medical-imaging-workflow",
        definition=workflow_definition,
        logs=sfn.LogOptions(
            destination=log_group,
            level=sfn.LogLevel.ALL,
        ),
    )
    
    return state_machine
