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
    create_patient_records_table,
    create_imaging_metadata_table,
    create_analysis_results_table,
    create_clinic_configs_table
)

from .roles.create_roles import (
    create_lambda_roles,
    create_pipes_role_for_dynamodb_stream_to_sqs,
    create_events_to_stepfunctions_role,
    create_lambda_dynamodb_role,
)

from .lambdas.create_lambdas import (
    create_image_processor,
    create_metadata_extractor,
    create_ai_analyzer,
    create_report_generator
)
from .lambdas.layers import create_layers
from .lambdas.define_io import assign_s3_event_source, assign_sqs_event_source

from .step_functions.create_state_machine import create_imaging_state_machine
from .sqs.create_sqs import create_analysis_queue, create_s3_upload_queue
from .eventbridge.create_rules import create_scheduler_rule
from .eventbridge.create_pipes import create_metadata_pipe, create_results_pipe


class MedicalImagingStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment: str = "dev", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define the S3 buckets
        s3_images_bucket = s3.Bucket(
            self,
            "medical-imaging-files-dev" if environment == "dev" else "medical-imaging-files",
            bucket_name="medical-imaging-files-dev" if environment == "dev" else "medical-imaging-files",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        
        # Define the DynamoDB tables via factory
        patient_records_table = create_patient_records_table(self)
        imaging_metadata_table = create_imaging_metadata_table(self)
        analysis_results_table = create_analysis_results_table(self)
        clinic_configs_table = create_clinic_configs_table(self)
        
        # Define the Lambda roles
        lambda_role = create_lambda_roles(self)
        metadata_processor_role = create_lambda_dynamodb_role(
            self, 
            id="MetadataProcessorRole", 
            table=imaging_metadata_table, 
            description="IAM role for a Lambda function to access DynamoDB"
        )
        
        # Metadata processor also needs access to PatientRecords table to query patient data
        patient_records_table.grant_read_write_data(cast(iam.IRole, metadata_processor_role))
        
        # Image processor needs access to PatientRecords table to batch write data
        patient_records_table.grant_read_write_data(lambda_role)
        
        # Create Queues; SQS
        analysis_queue, analysis_queue_dlq = create_analysis_queue(self, role=lambda_role)
        s3_upload_queue, s3_upload_queue_dlq = create_s3_upload_queue(self, role=lambda_role)
        
        # Create Pipes; EventBridge with least-privilege Pipes roles
        pipes_role_metadata = create_pipes_role_for_dynamodb_stream_to_sqs(
            self,
            id="PipesRoleMetadataToS3Upload",
            source_table=imaging_metadata_table,
            target_queue=s3_upload_queue,
        )
        pipes_role_results = create_pipes_role_for_dynamodb_stream_to_sqs(
            self,
            id="PipesRoleResultsToAnalysis",
            source_table=analysis_results_table,
            target_queue=analysis_queue,
        )
        metadata_pipe = create_metadata_pipe(
            self,
            metadata_table=imaging_metadata_table,
            s3_upload_queue=s3_upload_queue,
            role_arn=pipes_role_metadata.role_arn,
        )
        results_pipe = create_results_pipe(
            self,
            results_table=analysis_results_table,
            analysis_queue=analysis_queue,
            role_arn=pipes_role_results.role_arn,
        )
        
        # Define the Lambda functions
        layers = create_layers(self)
        metadata_extractor = create_metadata_extractor(self, role=lambda_role, layers=layers)
        image_processor = create_image_processor(self, role=lambda_role, layers=layers)
        ai_analyzer = create_ai_analyzer(self, role=lambda_role, layers=layers)
        report_generator = create_report_generator(self, role=lambda_role, layers=layers)
        
        # Attach queues to lambdas
        assign_sqs_event_source(image_processor, s3_upload_queue)
        assign_s3_event_source(ai_analyzer, s3_images_bucket)
        assign_sqs_event_source(report_generator, analysis_queue)
        
        # Create CloudWatch Log Group for Step Functions
        sfn_log_group = logs.LogGroup(
            self,
            f"MedicalImagingAnalysisLogs",
            log_group_name="/aws/vendedlogs/states/medical-imaging-analysis-logs",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Define the Step Function state machine
        imaging_state_machine = create_imaging_state_machine(
            self, 
            metadata_extractor_fn=metadata_extractor,
            image_processor_fn=image_processor, 
            ai_analyzer_fn=ai_analyzer,
            log_group=sfn_log_group
        )
        
        # Grant DynamoDB scan permission to state machine role for SDK integration
        clinic_configs_table.grant_read_data(imaging_state_machine.role)
        
        # Grant Lambda invoke permissions to state machine role for Lambda task invocations
        metadata_extractor.grant_invoke(imaging_state_machine.role)
        image_processor.grant_invoke(imaging_state_machine.role)
        ai_analyzer.grant_invoke(imaging_state_machine.role)
        
        # EventBridge rule to trigger the imaging state machine on schedule using dedicated role
        events_to_sfn_role = create_events_to_stepfunctions_role(
            self,
            id="EventsToSfnRoleMedicalImaging",
            state_machine=imaging_state_machine,
        )
        create_scheduler_rule(
            self,
            state_machine=imaging_state_machine,
            role=cast(iam.IRole, events_to_sfn_role),
        )
