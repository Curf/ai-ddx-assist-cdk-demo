from aws_cdk import (
    aws_sqs as sqs,
    Duration,
    aws_iam as iam,
)
from constructs import Construct
from typing import Tuple


def create_composition_queue(scope: Construct, role: iam.IRole) -> Tuple[sqs.Queue, sqs.Queue]:
    """
    Create an SQS queue for composition creation processing with a corresponding DLQ.
    
    This queue receives messages from DdxAssistResults table inserts and triggers the
    CreateComposition Lambda function to post results back to the EHR API.
    
    Returns:
        Tuple containing the main queue and its dead-letter queue
    """
    # Create dead-letter queue first
    composition_dlq = sqs.Queue(
        scope,
        "CompositionQueueDLQ",
        queue_name="ddx-assist-composition-dlq",
        retention_period=Duration.days(14),  # Keep messages for investigation
    )

    # Create main queue with reference to DLQ
    composition_queue = sqs.Queue(
        scope,
        "CompositionQueue",
        queue_name="ddx-assist-composition-queue",
        visibility_timeout=Duration.seconds(300),  # 5 minutes to process a message
        dead_letter_queue=sqs.DeadLetterQueue(
            max_receive_count=3,  # After 3 failed attempts, send to DLQ
            queue=composition_dlq,
        ),
    )

    # Grant permissions to the role to use the queue
    composition_queue.grant_send_messages(role)
    composition_queue.grant_consume_messages(role)

    return composition_queue, composition_dlq


def create_s3_upload_queue(scope: Construct, role: iam.IRole) -> Tuple[sqs.Queue, sqs.Queue]:
    """
    Create an SQS queue for S3 upload notifications with a corresponding DLQ.
    
    This queue receives messages from DocumentWatch table inserts and triggers the
    DownloadImage Lambda function to download medical images using pre-signed URLs.
    
    Returns:
        Tuple containing the main queue and its dead-letter queue
    """
    # Create dead-letter queue first
    s3_upload_dlq = sqs.Queue(
        scope,
        "S3UploadQueueDLQ",
        queue_name="mod-med-s3-upload-dlq",
        retention_period=Duration.days(14),
    )

    # Create main queue with reference to DLQ
    s3_upload_queue = sqs.Queue(
        scope,
        "S3UploadQueue",
        queue_name="mod-med-s3-upload-queue",
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
