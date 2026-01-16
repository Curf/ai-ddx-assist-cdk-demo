from aws_cdk import (
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_sqs as sqs,
    aws_stepfunctions as sfn,
)
from constructs import Construct


def create_lambda_roles(scope: Construct) -> iam.Role:
    """Create a default Lambda role with common permissions for medical imaging operations."""
    role = iam.Role(
        scope,
        "LambdaExecutionRole",
        assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        description="Default execution role for Lambda functions",
    )

    # Add managed policies for Lambda execution and S3 access
    role.add_managed_policy(
        iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
    )
    role.add_managed_policy(
        iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")
    )

    # Add S3 permissions for writing to buckets
    role.add_to_policy(
        iam.PolicyStatement(
            actions=[
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:GetObject",
                "s3:GetObjectAcl",
            ],
            resources=["arn:aws:s3:::medical-imaging-files*/*"],
        )
    )

    return role


def create_lambda_dynamodb_role(
    scope: Construct, id: str, table: dynamodb.Table, description: str
) -> iam.Role:
    """Create a Lambda role with specific DynamoDB permissions."""
    role = iam.Role(
        scope,
        id,
        assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        description=description,
    )

    # Add managed policy for Lambda execution
    role.add_managed_policy(
        iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
    )

    # Grant permission to the specific DynamoDB table
    table.grant_read_write_data(role)

    return role


def create_pipes_role_for_dynamodb_stream_to_sqs(
    scope: Construct, id: str, source_table: dynamodb.Table, target_queue: sqs.Queue
) -> iam.Role:
    """Create a role for EventBridge Pipes to connect DynamoDB streams to SQS queues."""
    role = iam.Role(
        scope,
        id,
        assumed_by=iam.ServicePrincipal("pipes.amazonaws.com"),
        description=f"Role for EventBridge Pipes from DynamoDB to SQS",
    )

    # Grant permissions to read from DynamoDB stream
    role.add_to_policy(
        iam.PolicyStatement(
            actions=[
                "dynamodb:DescribeStream",
                "dynamodb:GetRecords",
                "dynamodb:GetShardIterator",
                "dynamodb:ListStreams",
            ],
            resources=[source_table.table_stream_arn],
        )
    )

    # Grant permissions to write to SQS queue
    target_queue.grant_send_messages(role)

    return role


def create_events_to_stepfunctions_role(
    scope: Construct, id: str, state_machine: sfn.StateMachine
) -> iam.Role:
    """Create a role for EventBridge to trigger Step Functions."""
    role = iam.Role(
        scope,
        id,
        assumed_by=iam.ServicePrincipal("events.amazonaws.com"),
        description="Role for EventBridge to trigger Step Functions",
    )

    # Grant permission to execute the state machine
    role.add_to_policy(
        iam.PolicyStatement(
            actions=["states:StartExecution"],
            resources=[state_machine.state_machine_arn],
        )
    )

    return role
