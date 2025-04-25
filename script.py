import boto3
import os
import subprocess
from zipfile import ZipFile
from botocore.exceptions import ClientError
import argparse
import time

# Set up the AWS clients
s3 = boto3.client('s3')
cloudformation = boto3.client('cloudformation')

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Deploy Lambda function to S3.")
    parser.add_argument('--lambda-directory', required=True, help="Directory containing the Lambda function code")
    parser.add_argument('--zip-file-path', required=True, help="Path to the output ZIP file")
    parser.add_argument('--lambda-code-bucket', required=True, help="S3 bucket name to store Lambda code")
    parser.add_argument('--zip-file-key', required=True, help="Key (path) for the file in the S3 bucket")
    parser.add_argument('--region', required=True, help="AWS region where the bucket is located (e.g., us-east-1)")
    
    # Parameters for CloudFormation stack and file upload
    parser.add_argument('--stack-name', required=True, help="CloudFormation stack name")
    parser.add_argument('--template', required=True, help="Path to CloudFormation template")
    parser.add_argument('--source-bucket', required=True, help="Source S3 bucket name")
    parser.add_argument('--destination-bucket', required=True, help="Destination S3 bucket name")
    parser.add_argument('--test-file', required=True, help="Path to the test file to upload to S3")

    return parser.parse_args()

def zip_lambda_function(lambda_directory, zip_file_path):
    """Zips the contents of the Lambda function directory."""
    try:
        with ZipFile(zip_file_path, 'w') as zipf:
            for root, dirs, files in os.walk(lambda_directory):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), lambda_directory))
        print(f"Lambda function code zipped successfully to {zip_file_path}.")
    except Exception as e:
        print(f"Error zipping the Lambda function code: {e}")
        raise

def create_s3_bucket_if_not_exists(bucket_name, region):
    """Creates an S3 bucket if it doesn't already exist."""
    try:
        s3.head_bucket(Bucket=bucket_name)  # Check if the bucket exists
        print(f"Bucket '{bucket_name}' already exists.")
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"Bucket '{bucket_name}' does not exist. Creating now...")
            # Create the bucket with the specified region
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}  # Specify the region
            )
            print(f"Bucket '{bucket_name}' created.")
        else:
            print(f"Error checking or creating bucket: {e}")
            raise e

def upload_zip_to_s3(bucket_name, zip_file_path, zip_file_key):
    """Uploads the ZIP file to the S3 bucket if it doesn't already exist."""
    try:
        # Check if the file already exists in S3
        s3.head_object(Bucket=bucket_name, Key=zip_file_key)
        print(f"File '{zip_file_key}' already exists in bucket '{bucket_name}'.")
    except s3.exceptions.ClientError as e:
        # If the file does not exist, upload the file
        print(f"Uploading file '{zip_file_key}' to bucket '{bucket_name}'...")
        s3.upload_file(zip_file_path, bucket_name, zip_file_key)
        print(f"File '{zip_file_key}' uploaded successfully.")

def check_stack_exists(stack_name):
    """Check if the CloudFormation stack exists."""
    try:
        response = cloudformation.describe_stacks(StackName=stack_name)
        return True  # Stack exists
    except cloudformation.exceptions.ClientError as e:
        if 'does not exist' in str(e):
            return False  # Stack does not exist
        else:
            raise e  # Re-raise any other error

def wait_for_stack_creation(stack_name):
    """Waits until the CloudFormation stack has been created or updated."""
    print(f"Waiting for CloudFormation stack '{stack_name}' to be created/updated...")
    while True:
        try:
            response = cloudformation.describe_stacks(StackName=stack_name)
            stack_status = response['Stacks'][0]['StackStatus']
            print(f"Current stack status: {stack_status}")
            if stack_status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                print(f"Stack '{stack_name}' created/updated successfully.")
                break
            elif stack_status in ['CREATE_FAILED', 'UPDATE_FAILED']:
                print(f"Stack creation/update failed. Status: {stack_status}")
                raise Exception(f"Stack creation/update failed: {stack_status}")
            time.sleep(30)  # Wait before checking again
        except Exception as e:
            print(f"Error while checking stack status: {e}")
            raise

def run_aws_cli_command(command):
    """Run the AWS CLI command."""
    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"Error running command: {' '.join(command)}")
        print(f"Error: {result.stderr.decode()}")
        raise Exception(f"Command failed: {' '.join(command)}")
    
    print(result.stdout.decode())  # Print successful output

def upload_file_to_s3(file_path, bucket_name, file_key, region):
    """Uploads a file to S3."""
    print(f"Uploading file '{file_path}' to S3 bucket '{bucket_name}' at key '{file_key}'...")
    s3.upload_file(file_path, bucket_name, file_key, ExtraArgs={'ACL': 'private'})
    print(f"File '{file_path}' uploaded successfully to '{bucket_name}/{file_key}'.")

def main():
    # Parse arguments from CLI
    args = parse_args()

    # Step 1: Create a ZIP file of the Lambda function code
    zip_lambda_function(args.lambda_directory, args.zip_file_path)

    # Step 2: Create the S3 bucket (for Lambda code) if it doesn't exist
    create_s3_bucket_if_not_exists(args.lambda_code_bucket, args.region)

    # Step 3: Upload the ZIP file to the S3 bucket if it doesn't already exist
    upload_zip_to_s3(args.lambda_code_bucket, args.zip_file_path, args.zip_file_key)

    # Step 4: Check if the CloudFormation stack exists and either create or update the stack
    stack_exists = check_stack_exists(args.stack_name)

    aws_cli_command = [
        'aws', 'cloudformation', 'create-stack' if not stack_exists else 'update-stack',
        '--stack-name', args.stack_name,
        '--template-body', f'file://{args.template}',
        '--capabilities', 'CAPABILITY_IAM',
        '--parameters',
        f'ParameterKey=SourceBucketName,ParameterValue={args.source_bucket}',
        f'ParameterKey=DestinationBucketName,ParameterValue={args.destination_bucket}',
        f'ParameterKey=LambdaCodeBucketName,ParameterValue={args.lambda_code_bucket}'
    ]

    run_aws_cli_command(aws_cli_command)

    # Step 5: Wait for CloudFormation stack creation or update to complete
    wait_for_stack_creation(args.stack_name)

    # Step 6: Upload the test file to the source bucket
    upload_file_to_s3(args.test_file, args.source_bucket, os.path.basename(args.test_file), args.region)

if __name__ == "__main__":
    main()


