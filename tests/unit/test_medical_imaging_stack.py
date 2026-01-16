import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template

from medical_imaging_cdk.medical_imaging_stack import MedicalImagingStack


def test_stack_creates_resources():
    # Create app and stack
    app = cdk.App()
    stack = MedicalImagingStack(app, "TestStack", environment="dev")
    
    # Prepare the stack for assertions
    template = Template.from_stack(stack)
    
    # Verify DynamoDB tables are created
    template.resource_count_is("AWS::DynamoDB::Table", 4)
    
    # Verify Lambda functions are created
    template.resource_count_is("AWS::Lambda::Function", 4)
    
    # Verify S3 bucket is created
    template.resource_count_is("AWS::S3::Bucket", 1)
    
    # Verify SQS queues are created (including DLQs)
    template.resource_count_is("AWS::SQS::Queue", 4)
    
    # Verify Step Functions state machine is created
    template.resource_count_is("AWS::StepFunctions::StateMachine", 1)
    
    # Verify IAM roles are created
    template.resource_count_is("AWS::IAM::Role", 5)  # Adjust as needed based on exact role count


def test_step_functions_state_machine():
    # Create app and stack
    app = cdk.App()
    stack = MedicalImagingStack(app, "TestStack", environment="dev")
    
    # Prepare the stack for assertions
    template = Template.from_stack(stack)
    
    # Check that the state machine exists with expected properties
    template.has_resource("AWS::StepFunctions::StateMachine", {
        "Properties": {
            "StateMachineName": "medical-imaging-workflow"
        }
    })


def test_s3_bucket_configuration():
    # Create app and stack
    app = cdk.App()
    stack = MedicalImagingStack(app, "TestStack", environment="dev")
    
    # Prepare the stack for assertions
    template = Template.from_stack(stack)
    
    # Check that S3 bucket has expected properties
    template.has_resource("AWS::S3::Bucket", {
        "Properties": {
            "BucketName": "medical-imaging-files-dev"
        }
    })
