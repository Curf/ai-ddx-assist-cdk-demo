from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct


def create_encounter_watch_table(scope: Construct) -> dynamodb.Table:
    """Create and return the EncounterWatch DynamoDB table with GSIs."""
    table = dynamodb.Table(
        scope,
        "EncounterWatch",
        partition_key=dynamodb.Attribute(
            name="encounterId",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="patientId",
            type=dynamodb.AttributeType.STRING,
        ),
        table_name="EncounterWatch",
        stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,  # Use on-demand to handle variable workloads
    )

    table.add_global_secondary_index(
        index_name="EncounterFirmNextPoll",
        partition_key=dynamodb.Attribute(
            name="firmId",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="nextPollAt",
            type=dynamodb.AttributeType.NUMBER,
        ),
        projection_type=dynamodb.ProjectionType.ALL,
    )

    table.add_global_secondary_index(
        index_name="EncounterStatusNextPoll",
        partition_key=dynamodb.Attribute(
            name="encounterStatus",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="nextPollAt",
            type=dynamodb.AttributeType.NUMBER,
        ),
        projection_type=dynamodb.ProjectionType.ALL,
    )
    
    return table


def create_document_watch_table(scope: Construct) -> dynamodb.Table:
    """Create and return the DocumentWatch DynamoDB table with GSIs."""
    table = dynamodb.Table(
        scope,
        "DocumentWatch",
        partition_key=dynamodb.Attribute(
            name="fileId",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="firmId",
            type=dynamodb.AttributeType.STRING,
        ),
        table_name="DocumentWatch",
        stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
    )

    table.add_global_secondary_index(
        index_name="PatientFirm",
        partition_key=dynamodb.Attribute(
            name="patientId",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="firmId",
            type=dynamodb.AttributeType.STRING,
        ),
        projection_type=dynamodb.ProjectionType.ALL,
    )

    return table


def create_ddx_results_table(scope: Construct) -> dynamodb.Table:
    """Create and return the DdxAssistResults DynamoDB table with GSIs."""
    table = dynamodb.Table(
        scope,
        "DdxAssistResults",
        partition_key=dynamodb.Attribute(
            name="fileId",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="firmId",
            type=dynamodb.AttributeType.STRING,
        ),
        table_name="DdxAssistResults",
        stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
    )

    table.add_global_secondary_index(
        index_name="PatientFirm",
        partition_key=dynamodb.Attribute(
            name="patientId",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="firmId",
            type=dynamodb.AttributeType.STRING,
        ),
        projection_type=dynamodb.ProjectionType.ALL,
    )

    return table


def create_firm_configs_table(scope: Construct) -> dynamodb.Table:
    """Create and return the company-config-table DynamoDB table with GSIs."""
    table = dynamodb.Table(
        scope,
        "company-config-table",
        partition_key=dynamodb.Attribute(
            name="firmName",
            type=dynamodb.AttributeType.STRING,
        ),
        table_name="company-config-table",
    )
    return table


def create_practitioner_whitelist_table(scope: Construct) -> dynamodb.Table:
    """Create and return the PractitionerWhitelist DynamoDB table."""
    table = dynamodb.Table(
        scope,
        "PractitionerWhitelist",
        partition_key=dynamodb.Attribute(
            name="id",
            type=dynamodb.AttributeType.STRING,
        ),
        table_name="PractitionerWhitelist",
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
    )
    return table
