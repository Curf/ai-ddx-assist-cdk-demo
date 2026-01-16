from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct


def create_patient_records_table(scope: Construct) -> dynamodb.Table:
    """Create and return the PatientRecords DynamoDB table with GSIs."""
    table = dynamodb.Table(
        scope,
        "PatientRecords",
        partition_key=dynamodb.Attribute(
            name="patientId",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="recordType",
            type=dynamodb.AttributeType.STRING,
        ),
        table_name="PatientRecords",
        stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,  # Use on-demand to handle variable workloads
    )

    table.add_global_secondary_index(
        index_name="PatientClinicSchedule",
        partition_key=dynamodb.Attribute(
            name="clinicId",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="scheduledTime",
            type=dynamodb.AttributeType.NUMBER,
        ),
        projection_type=dynamodb.ProjectionType.ALL,
    )

    table.add_global_secondary_index(
        index_name="PatientStatusSchedule",
        partition_key=dynamodb.Attribute(
            name="patientStatus",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="scheduledTime",
            type=dynamodb.AttributeType.NUMBER,
        ),
        projection_type=dynamodb.ProjectionType.ALL,
    )

    return table


def create_imaging_metadata_table(scope: Construct) -> dynamodb.Table:
    """Create and return the ImagingMetadata DynamoDB table with GSIs."""
    table = dynamodb.Table(
        scope,
        "ImagingMetadata",
        partition_key=dynamodb.Attribute(
            name="imageId",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="clinicId",
            type=dynamodb.AttributeType.STRING,
        ),
        table_name="ImagingMetadata",
        stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
    )

    table.add_global_secondary_index(
        index_name="PatientClinic",
        partition_key=dynamodb.Attribute(
            name="patientId",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="clinicId",
            type=dynamodb.AttributeType.STRING,
        ),
        projection_type=dynamodb.ProjectionType.ALL,
    )

    return table


def create_analysis_results_table(scope: Construct) -> dynamodb.Table:
    """Create and return the AnalysisResults DynamoDB table with GSIs."""
    table = dynamodb.Table(
        scope,
        "AnalysisResults",
        partition_key=dynamodb.Attribute(
            name="imageId",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="clinicId",
            type=dynamodb.AttributeType.STRING,
        ),
        table_name="AnalysisResults",
        stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
    )

    table.add_global_secondary_index(
        index_name="PatientClinic",
        partition_key=dynamodb.Attribute(
            name="patientId",
            type=dynamodb.AttributeType.STRING,
        ),
        sort_key=dynamodb.Attribute(
            name="clinicId",
            type=dynamodb.AttributeType.STRING,
        ),
        projection_type=dynamodb.ProjectionType.ALL,
    )

    return table


def create_clinic_configs_table(scope: Construct) -> dynamodb.Table:
    """Create and return the clinic-config-table DynamoDB table."""
    table = dynamodb.Table(
        scope,
        "clinic-config-table",
        partition_key=dynamodb.Attribute(
            name="clinicName",
            type=dynamodb.AttributeType.STRING,
        ),
        table_name="clinic-config-table",
    )
    return table
