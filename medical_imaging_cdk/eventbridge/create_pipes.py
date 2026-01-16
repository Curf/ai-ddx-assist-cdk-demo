from aws_cdk import (
    aws_pipes as pipes,
    aws_dynamodb as dynamodb,
    aws_sqs as sqs,
)
from constructs import Construct


def create_metadata_pipe(
    scope: Construct,
    metadata_table: dynamodb.Table,
    s3_upload_queue: sqs.Queue,
    role_arn: str,
) -> pipes.CfnPipe:
    """
    Create an EventBridge Pipe that connects DynamoDB streams from the metadata table to an SQS queue.
    
    This pipe forwards new image metadata entries to the S3 upload processing queue.
    
    Args:
        scope: The CDK construct scope
        metadata_table: Source DynamoDB table with stream enabled
        s3_upload_queue: Target SQS queue for processing
        role_arn: ARN of the IAM role with permissions for the pipe
        
    Returns:
        The created EventBridge pipe
    """
    # Create pipe connecting DynamoDB stream to SQS
    pipe = pipes.CfnPipe(
        scope,
        "MetadataToS3UploadPipe",
        name="metadata-to-s3-upload-pipe",
        role_arn=role_arn,
        source=f"arn:aws:dynamodb:{scope.region}:{scope.account}:table/{metadata_table.table_name}/stream/*",
        source_parameters=pipes.CfnPipe.PipeSourceParametersProperty(
            dynamodb_stream_parameters=pipes.CfnPipe.PipeSourceDynamoDBStreamParametersProperty(
                starting_position="LATEST",
                batch_size=1,
                dead_letter_config=pipes.CfnPipe.PipeTargetDeadLetterConfigProperty(
                    type="SQS",
                ),
            ),
            filter_criteria=pipes.CfnPipe.FilterCriteriaProperty(
                filters=[
                    pipes.CfnPipe.FilterProperty(
                        pattern='{"eventName": ["INSERT", "MODIFY"], "dynamodb": {"NewImage": {"status": {"S": ["NEW"]}}}}',
                    )
                ]
            ),
        ),
        target=s3_upload_queue.queue_arn,
        target_parameters=pipes.CfnPipe.PipeTargetParametersProperty(
            sqs_queue_parameters=pipes.CfnPipe.PipeTargetSqsQueueParametersProperty(
                message_deduplication_id="$.dynamodb.NewImage.imageId.S",
                message_group_id="imaging-metadata",
            ),
            input_template="""
            {
                "imageId": <$.dynamodb.NewImage.imageId.S>,
                "patientId": <$.dynamodb.NewImage.patientId.S>,
                "clinicId": <$.dynamodb.NewImage.clinicId.S>,
                "imageType": <$.dynamodb.NewImage.imageType.S>,
                "s3Key": <$.dynamodb.NewImage.s3Key.S>,
                "timestamp": <$.dynamodb.NewImage.timestamp.N>
            }
            """,
        ),
    )
    
    return pipe


def create_results_pipe(
    scope: Construct,
    results_table: dynamodb.Table,
    analysis_queue: sqs.Queue,
    role_arn: str,
) -> pipes.CfnPipe:
    """
    Create an EventBridge Pipe that connects DynamoDB streams from the results table to an SQS queue.
    
    This pipe forwards new analysis results to the report generation queue.
    
    Args:
        scope: The CDK construct scope
        results_table: Source DynamoDB table with stream enabled
        analysis_queue: Target SQS queue for processing
        role_arn: ARN of the IAM role with permissions for the pipe
        
    Returns:
        The created EventBridge pipe
    """
    # Create pipe connecting DynamoDB stream to SQS
    pipe = pipes.CfnPipe(
        scope,
        "ResultsToAnalysisQueuePipe",
        name="results-to-analysis-queue-pipe",
        role_arn=role_arn,
        source=f"arn:aws:dynamodb:{scope.region}:{scope.account}:table/{results_table.table_name}/stream/*",
        source_parameters=pipes.CfnPipe.PipeSourceParametersProperty(
            dynamodb_stream_parameters=pipes.CfnPipe.PipeSourceDynamoDBStreamParametersProperty(
                starting_position="LATEST",
                batch_size=1,
                dead_letter_config=pipes.CfnPipe.PipeTargetDeadLetterConfigProperty(
                    type="SQS",
                ),
            ),
            filter_criteria=pipes.CfnPipe.FilterCriteriaProperty(
                filters=[
                    pipes.CfnPipe.FilterProperty(
                        pattern='{"eventName": ["INSERT", "MODIFY"], "dynamodb": {"NewImage": {"status": {"S": ["ANALYZED"]}}}}',
                    )
                ]
            ),
        ),
        target=analysis_queue.queue_arn,
        target_parameters=pipes.CfnPipe.PipeTargetParametersProperty(
            sqs_queue_parameters=pipes.CfnPipe.PipeTargetSqsQueueParametersProperty(
                message_deduplication_id="$.dynamodb.NewImage.imageId.S",
                message_group_id="analysis-results",
            ),
            input_template="""
            {
                "imageId": <$.dynamodb.NewImage.imageId.S>,
                "patientId": <$.dynamodb.NewImage.patientId.S>,
                "clinicId": <$.dynamodb.NewImage.clinicId.S>,
                "findings": <$.dynamodb.NewImage.findings.S>,
                "confidence": <$.dynamodb.NewImage.confidence.N>,
                "timestamp": <$.dynamodb.NewImage.timestamp.N>
            }
            """,
        ),
    )
    
    return pipe
