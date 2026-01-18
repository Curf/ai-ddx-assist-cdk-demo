from typing import Optional
from constructs import Construct
from aws_cdk import (
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_stepfunctions as sfn,
    aws_iam as iam,
)


def create_poller_state_machine(
    scope: Construct,
    *,
    refresh_creds_fn: lambda_.Function,
    encounter_poller_fn: lambda_.Function,
    document_poller_fn: lambda_.Function,
    state_machine_name: str = "ai-ddx-assist-poller",
    log_group: Optional[logs.ILogGroup] = None,
    role: Optional[iam.IRole] = None,  # If you already have a role; otherwise let CDK create one
) -> sfn.StateMachine:
    """
    Instantiate the Step Functions State Machine from ASL file with lambda ARN substitutions.
    Expects template at: medical_imaging_cdk/step_functions/template.yaml
    """
    definition = sfn.DefinitionBody.from_file(
        "medical_imaging_cdk/step_functions/template.yaml"
    )
    substitutions = {
        "PLACEHOLDER_FUNCTION_ARN_1": refresh_creds_fn.function_arn,
        "PLACEHOLDER_FUNCTION_ARN_2": encounter_poller_fn.function_arn,
        "PLACEHOLDER_FUNCTION_ARN_3": document_poller_fn.function_arn,
    }

    logs_config = None
    if log_group:
        logs_config = sfn.LogOptions(
            destination=log_group,
            level=sfn.LogLevel.ALL,
            include_execution_data=True,
        )

    return sfn.StateMachine(
        scope,
        "AiDdxAssistPollerStateMachine",
        state_machine_name=state_machine_name,
        definition_body=definition,
        definition_substitutions=substitutions,
        state_machine_type=sfn.StateMachineType.EXPRESS,
        logs=logs_config,
        role=role,  # optional
        tracing_enabled=True,
    )
