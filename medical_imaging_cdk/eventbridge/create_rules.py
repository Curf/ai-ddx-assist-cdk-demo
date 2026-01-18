from aws_cdk import (
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_stepfunctions as sfn,
)
from constructs import Construct


def create_scheduler_rule(scope: Construct, state_machine: sfn.StateMachine, role: iam.IRole) -> events.Rule:
    """
    Create an EventBridge rule to trigger the medical imaging processing state machine on a schedule.
    
    Args:
        scope: The CDK construct scope
        state_machine: The Step Function state machine to trigger
        role: IAM role with permissions to start the state machine
        
    Returns:
        The created EventBridge rule
    """
    # Create a scheduled rule that triggers every minute
    rule = events.Rule(
        scope,
        "ImagingProcessorScheduler",
        schedule=events.Schedule.cron(minute="*/1"),
        description="Triggers the medical imaging processor state machine every minute",
    )
    
    # Add target to invoke the state machine when the rule triggers
    rule.add_target(
        targets.SfnStateMachine(
            state_machine,
            role=role,
            input=events.RuleTargetInput.from_object(
                {
                    "time": events.EventField.time,
                    "region": events.EventField.region,
                    "source": "aws.events",
                    "detail-type": "Scheduled Event"
                }
            ),
        )
    )
    
    return rule
