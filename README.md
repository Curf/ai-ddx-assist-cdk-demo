# Medical Imaging Analysis Pipeline - AWS CDK

This project demonstrates an AWS CDK implementation of a serverless architecture for medical imaging analysis using AI. The infrastructure processes and analyzes medical images to assist healthcare professionals with diagnostic insights.

## Architecture Overview

The solution uses a combination of AWS services to create a scalable, event-driven pipeline:

- **AWS Lambda**: Serverless functions to process images, analyze data, and generate reports
- **Amazon DynamoDB**: NoSQL database for storing patient records, image metadata, and analysis results
- **Amazon S3**: Object storage for medical images
- **AWS Step Functions**: Orchestrates the workflow between components
- **Amazon EventBridge**: Manages event-driven processes and scheduling
- **Amazon SQS**: Message queuing for asynchronous processing

## System Flow

1. **Data Collection**: Medical images are uploaded or referenced for processing
2. **Image Processing**: Lambda functions retrieve and prepare images for analysis
3. **AI Analysis**: Images are analyzed by AI services to identify potential diagnoses
4. **Results Storage**: Analysis results are stored in DynamoDB
5. **Report Generation**: Clinical reports are created based on the AI analysis
6. **Notification**: Healthcare providers are notified when results are ready

## Getting Started

### Prerequisites

- AWS CLI installed and configured
- Node.js 14.x or later
- Python 3.7 or later
- AWS CDK Toolkit

### Installation

1. Clone the repository
```
git clone https://github.com/yourusername/medical-imaging-analysis-cdk.git
cd medical-imaging-analysis-cdk
```

2. Create a Python virtual environment
```
python3 -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Deploy the CDK stack
```
cdk bootstrap
cdk deploy
```

## Development

### Project Structure

- `app.py`: Entry point for the CDK application
- `medical_imaging_cdk/`: Main CDK stack definition
  - `dynamodb/`: DynamoDB table definitions
  - `lambdas/`: Lambda function configurations
  - `step_functions/`: State machine definitions
  - `sqs/`: SQS queue configurations
  - `eventbridge/`: Event rules and schedules

### Useful Commands

* `cdk ls`          list all stacks in the app
* `cdk synth`       emits the synthesized CloudFormation template
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk docs`        open CDK documentation

## Security

This project is for demonstration purposes only. In a real-world scenario, you would need to implement:

- Encryption of sensitive patient data
- Fine-grained IAM permissions
- HIPAA compliance measures
- Regular security audits

## License

This project is licensed under the MIT License - see the LICENSE file for details.
