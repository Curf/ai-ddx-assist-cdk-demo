from aws_cdk import (
    aws_sqs as sqs,
    Duration,
    aws_iam as iam,
)
from constructs import Construct
from typing import Tuple


def create_analysis_queue(scope: Construct, role: iam.IRole) -> Tuple[sqs.Queue, sqs.Queue]:
    """
    Create an SQS queue for AI analysis results processing with a corresponding DLQ.
    
    Returns:
        Tuple containing the main queue and its dead-letter queue
    """
    # Create dead-letter queue first
    analysis_dlq = sqs.Queue(
        scope,
        "AnalysisQueueDLQ",
        queue_name="medical-imaging-analysis-dlq",
        retention_period=Duration.days(14),  # Keep messages for investigation
    )

    # Create main queue with reference to DLQ
    analysis_queue = sqs.Queue(
        scope,
        "AnalysisQueue",
        queue_name="medical-imaging-analysis-queue",
        visibility_timeout=Duration.seconds(300),  # 5 minutes to process a message
        dead_letter_queue=sqs.DeadLetterQueue(
            max_receive_count=3,  # After 3 failed attempts, send to DLQ
            queue=analysis_dlq,
        ),
    )

    # Grant permissions to the role to use the queue
    analysis_queue.grant_send_messages(role)
    analysis_queue.grant_consume_messages(role)

    return analysis_queue, analysis_dlq


def create_s3_upload_queue(scope: Construct, role: iam.IRole) -> Tuple[sqs.Queue, sqs.Queue]:
    """
    Create an SQS queue for S3 upload notifications with a corresponding DLQ.
    
    Returns:
        Tuple containing the main queue and its dead-letter queue
    """
    # Create dead-letter queue first
    s3_upload_dlq = sqs.Queue(
        scope,
        "S3UploadQueueDLQ",
        queue_name="medical-imaging-s3-upload-dlq",
        retention_period=Duration.days(14),
    )

    # Create main queue with reference to DLQ
    s3_upload_queue = sqs.Queue(
        scope,
        "S3UploadQueue",
        queue_name="medical-imaging-s3-upload-queue",
        visibility_timeout=Duration.seconds(180),  # 3 minutes to process a message
        dead_letter_queue=sqs.DeadLetterQueue(
            max_receive_count=3,
            queue=s3_upload_dlq,
        ),
    )

    # Grant permissions to the role to use the queue
    s3_upload_queue.grant_send_messages(role)
    s3_upload_queue.grant_consume_messages(role)

    return s3_upload_queue, s3_upload_dlq
