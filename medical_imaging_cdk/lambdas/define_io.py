from aws_cdk import (
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_event_sources,
    aws_s3 as s3,
    aws_sqs as sqs,
)


def assign_s3_event_source(lambda_function: lambda_.Function, bucket: s3.Bucket) -> None:
    """
    Configure an S3 event source for a Lambda function.
    This allows Lambda functions to be triggered on S3 events like object creation.
    """
    lambda_function.add_event_source(
        lambda_event_sources.S3EventSource(
            bucket,
            events=[s3.EventType.OBJECT_CREATED],
            filters=[
                s3.NotificationKeyFilter(
                    prefix="uploads/",
                    suffix=".jpg"
                )
            ]
        )
    )


def assign_sqs_event_source(lambda_function: lambda_.Function, queue: sqs.Queue) -> None:
    """
    Configure an SQS event source for a Lambda function.
    This allows Lambda functions to process messages from SQS queues.
    """
    lambda_function.add_event_source(
        lambda_event_sources.SqsEventSource(
            queue,
            batch_size=10,  # Process up to 10 messages per invocation
            max_batching_window=lambda_.Duration.seconds(30),  # Wait up to 30 seconds to collect messages
        )
    )
