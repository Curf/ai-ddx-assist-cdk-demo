from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_iam as iam,
    aws_logs as logs,
    RemovalPolicy,
)
from constructs import Construct
from typing import cast

from .dynamodb.create_tables import (
    create_encounter_watch_table,
    create_document_watch_table,
    create_ddx_results_table,
    create_firm_configs_table,
    create_practitioner_whitelist_table
)

from .roles.create_roles import (
    create_lambda_roles,
    create_pipes_role_for_dynamodb_stream_to_sqs,
    create_events_to_stepfunctions_role,
    create_lambda_dynamodb_role,
)

from .lambdas.create_lambdas import (
    create_refresh_creds,
    create_encounter_poller,
    create_document_poller,
    create_download_image,
    create_get_ddx_assist_inference,
    create_create_composition
)
from .lambdas.layers import create_layers
from .lambdas.define_io import assign_s3_event_source, assign_sqs_event_source

from .step_functions.create_state_machine import create_poller_state_machine
from .sqs.create_sqs import create_composition_queue, create_s3_upload_queue
from .eventbridge.create_rules import create_poller_rule
from .eventbridge.create_pipes import create_document_watch_pipe, create_ddx_results_pipe


class MedicalImagingStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment: str = "dev", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define the S3 buckets
        s3_upload_bucket = s3.Bucket(
            self,
            "mod-med-image-files-dev" if environment == "dev" else "mod-med-image-files",
            bucket_name="mod-med-image-files-dev" if environment == "dev" else "mod-med-image-files",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        
        # Define the DynamoDB tables via factory
        encounter_watch_table = create_encounter_watch_table(self)
        document_watch_table = create_document_watch_table(self)
        ddx_results_table = create_ddx_results_table(self)
        firm_configs_table = create_firm_configs_table(self)
        practitioner_whitelist_table = create_practitioner_whitelist_table(self)
        
        # Define the Lambda roles
        lambda_role = create_lambda_roles(self)
        document_poller_role = create_lambda_dynamodb_role(self, 
                                                           id="DocumentPollerRole", 
                                                           table=document_watch_table, 
                                                           description="IAM role for a Lambda function to access DynamoDB")
        
        # Document-Poller also needs access to EncounterWatch table to query encounters
        encounter_watch_table.grant_read_write_data(cast(iam.IRole, document_poller_role))
        
        # Encounter-Poller needs access to EncounterWatch table to batch write encounters
        encounter_watch_table.grant_read_write_data(lambda_role)
        
        # Encounter-Poller needs read access to PractitionerWhitelist table for filtering
        practitioner_whitelist_table.grant_read_data(lambda_role)
        
        # Create Queues; SQS
        composition_queue, composition_queue_dlq = create_composition_queue(self, role=lambda_role)
        s3_upload_queue, s3_upload_queue_dlq = create_s3_upload_queue(self, role=lambda_role)
        
        # Create Pipes; EventBridge with least-privilege Pipes roles
        pipes_role_doc = create_pipes_role_for_dynamodb_stream_to_sqs(
            self,
            id="PipesRoleDocumentWatchToS3Upload",
            source_table=document_watch_table,
            target_queue=s3_upload_queue,
        )
        pipes_role_ddx = create_pipes_role_for_dynamodb_stream_to_sqs(
            self,
            id="PipesRoleDdxResultsToComposition",
            source_table=ddx_results_table,
            target_queue=composition_queue,
        )
        document_watch_pipe = create_document_watch_pipe(
            self,
            document_watch_table=document_watch_table,
            s3_upload_queue=s3_upload_queue,
            role_arn=pipes_role_doc.role_arn,
        )
        ddx_results_pipe = create_ddx_results_pipe(
            self,
            ddx_results_table=ddx_results_table,
            composition_queue=composition_queue,
            role_arn=pipes_role_ddx.role_arn,
        )
        
        # Define the Lambda functions
        layers = create_layers(self)
        refresh_creds = create_refresh_creds(self, role=lambda_role, layers=layers)
        encounter_poller = create_encounter_poller(self, role=lambda_role, layers=layers)
        document_poller = create_document_poller(self, role=cast(iam.IRole, document_poller_role), layers=layers)
        download_image = create_download_image(self, role=lambda_role, layers=layers)
        get_ddx_assist_inference = create_get_ddx_assist_inference(self, role=lambda_role, layers=layers)
        create_composition = create_create_composition(self, role=lambda_role, layers=layers)
        
        # attach queues to lambdas
        assign_sqs_event_source(download_image, s3_upload_queue)
        assign_s3_event_source(get_ddx_assist_inference, s3_upload_bucket)
        assign_sqs_event_source(create_composition, composition_queue)
        
        # Create CloudWatch Log Group for Step Functions
        sfn_log_group = logs.LogGroup(
            self,
            f"AiDdxAssistPollerLogs",
            log_group_name="/aws/vendedlogs/states/ai-ddx-assist-poller-logs",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Define the Step Function state machine
        poller_state_machine = create_poller_state_machine(self, 
                                                           refresh_creds_fn=refresh_creds, 
                                                           encounter_poller_fn=encounter_poller, 
                                                           document_poller_fn=document_poller,
                                                           log_group=sfn_log_group)
        
        # Grant DynamoDB scan permission to state machine role for SDK integration
        firm_configs_table.grant_read_data(poller_state_machine.role)
        
        # Grant Lambda invoke permissions to state machine role for Lambda task invocations
        refresh_creds.grant_invoke(poller_state_machine.role)
        encounter_poller.grant_invoke(poller_state_machine.role)
        document_poller.grant_invoke(poller_state_machine.role)
        
        # EventBridge rule to trigger the poller state machine on schedule using dedicated role
        events_to_sfn_role = create_events_to_stepfunctions_role(
            self,
            id="EventsToSfnRoleModMedPollers",
            state_machine=poller_state_machine,
        )
        create_poller_rule(
            self,
            state_machine=poller_state_machine,
            role=cast(iam.IRole, events_to_sfn_role),
        )
