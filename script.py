import boto3
import os
import subprocess
import zipfile
from botocore.exceptions import ClientError
import argparse
import time
import io

s3 = boto3.client('s3')
cloudformation = boto3.client('cloudformation')

LAMBDA_CODE_BUCKET = "copylambdafuncbucket" 

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Deploy Lambda function to S3.")
    parser.add_argument('--lambda-file', required=True, help="Lambda function file (e.g., lambda.py)")
    parser.add_argument('--zip-file-key', required=True, help="Key (path) for the file in the S3 bucket")
    parser.add_argument('--region', required=True, help="AWS region where the bucket is located (e.g., us-east-1)")
    
    parser.add_argument('--stack-name', required=True, help="CloudFormation stack name")
    parser.add_argument('--template', required=True, help="Path to CloudFormation template")
    parser.add_argument('--source-bucket', required=True, help="Source S3 bucket name")
    parser.add_argument('--destination-bucket', required=True, help="Destination S3 bucket name")
    parser.add_argument('--test-file', required=True, help="Path to the test file to upload to S3")

    return parser.parse_args()


def create_in_memory_zip(lambda_file):
    """Creates a ZIP file in memory."""
    try:
        if not os.path.exists(lambda_file):
            print(f"Error: The file {lambda_file} does not exist.")
            return None

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(lambda_file, os.path.basename(lambda_file))
            print(f"Added {lambda_file} to in-memory ZIP.")

        zip_buffer.seek(0)

        return zip_buffer
    except Exception as e:
        print(f"Error creating in-memory ZIP: {e}")
        return None

def create_s3_bucket_if_not_exists(bucket_name, region):
    """Creates an S3 bucket if it doesn't already exist."""
    try:
        s3.head_bucket(Bucket=bucket_name)  
        print(f"Bucket '{bucket_name}' already exists.")
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"Bucket '{bucket_name}' does not exist. Creating now...")            
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region} 
            )
            print(f"Bucket '{bucket_name}' created.")
        else:
            print(f"Error checking or creating bucket: {e}")
            raise e

def upload_zip_to_s3(bucket_name, zip_buffer, zip_file_key):
    """Uploads the ZIP file to the S3 bucket if it doesn't already exist."""
    try:
        s3.head_object(Bucket=bucket_name, Key=zip_file_key)
        print(f"File '{zip_file_key}' already exists in bucket '{bucket_name}'.")
    except s3.exceptions.ClientError as e:
        print(f"Uploading in-memory ZIP file '{zip_file_key}' to bucket '{bucket_name}'...")
        s3.upload_fileobj(zip_buffer, bucket_name, zip_file_key)
        print(f"File '{zip_file_key}' uploaded successfully.")

def check_stack_exists(stack_name):
    """Check if the CloudFormation stack exists."""
    try:
        response = cloudformation.describe_stacks(StackName=stack_name)
        return True  
    except cloudformation.exceptions.ClientError as e:
        if 'does not exist' in str(e):
            return False  
        else:
            raise e  

def wait_for_stack_creation_or_update(stack_name, stack_exists, skip_waiting):
    """Wait for CloudFormation stack to be created or updated."""
    if skip_waiting:
        return  

    if stack_exists:
        print(f"Waiting for CloudFormation stack '{stack_name}' to be updated...")
        waiter = cloudformation.get_waiter('stack_update_complete')
    else:
        print(f"Waiting for CloudFormation stack '{stack_name}' to be created...")
        waiter = cloudformation.get_waiter('stack_create_complete')
    
    try:
        waiter.wait(StackName=stack_name)
        print(f"CloudFormation stack '{stack_name}' operation completed successfully.")
    except cloudformation.exceptions.WaiterError as e:
        print(f"Error while waiting for stack '{stack_name}': {e}")
        raise

def run_aws_boto3_command(stack_name, template, source_bucket, destination_bucket, lambda_code_bucket, stack_exists):
    """Run the CloudFormation command using Boto3 (create-stack or update-stack)."""
    skip_waiting = False  
    try:
        if not stack_exists:
            print(f"Creating CloudFormation stack '{stack_name}'...")
            response = cloudformation.create_stack(
                StackName=stack_name,
                TemplateBody=open(template, 'r').read(),
                Capabilities=['CAPABILITY_IAM'],
                Parameters=[
                    {'ParameterKey': 'SourceBucketName', 'ParameterValue': source_bucket},
                    {'ParameterKey': 'DestinationBucketName', 'ParameterValue': destination_bucket},
                    {'ParameterKey': 'LambdaCodeBucketName', 'ParameterValue': lambda_code_bucket}
                ]
            )
            print(f"CloudFormation stack '{stack_name}' creation initiated.")
        else:
            print(f"Updating CloudFormation stack '{stack_name}'...")
            try:
                response = cloudformation.update_stack(
                    StackName=stack_name,
                    TemplateBody=open(template, 'r').read(),
                    Capabilities=['CAPABILITY_IAM'],
                    Parameters=[
                        {'ParameterKey': 'SourceBucketName', 'ParameterValue': source_bucket},
                        {'ParameterKey': 'DestinationBucketName', 'ParameterValue': destination_bucket},
                        {'ParameterKey': 'LambdaCodeBucketName', 'ParameterValue': lambda_code_bucket}
                    ]
                )
                print(f"CloudFormation stack '{stack_name}' update initiated.")
            except cloudformation.exceptions.ClientError as e:
                if 'No updates are to be performed' in str(e):
                    print(f"CloudFormation stack '{stack_name}' is already up to date. No update necessary.")
                    skip_waiting = True 
                    return skip_waiting 
                else:
                    print(f"Error with CloudFormation stack '{stack_name}': {e}")
                    raise e
    except ClientError as e:
        print(f"Error with CloudFormation stack '{stack_name}': {e}")
        raise e

    return skip_waiting  

def upload_file_to_s3(file_path, bucket_name, file_key, region):
    """Uploads a file to S3."""
    print(f"Uploading file '{file_path}' to S3 bucket '{bucket_name}' at key '{file_key}'...")
    s3.upload_file(file_path, bucket_name, file_key, ExtraArgs={'ACL': 'private'})
    print(f"File '{file_path}' uploaded successfully to '{bucket_name}/{file_key}'.")

def main():
    args = parse_args()

    zip_buffer = create_in_memory_zip(args.lambda_file)
    if not zip_buffer:
        print("Failed to create in-memory ZIP file. Exiting...")
        return
    
    create_s3_bucket_if_not_exists(LAMBDA_CODE_BUCKET, args.region)

    upload_zip_to_s3(LAMBDA_CODE_BUCKET, zip_buffer, args.zip_file_key)

    stack_exists = check_stack_exists(args.stack_name)

    skip_waiting = run_aws_boto3_command(args.stack_name, args.template, args.source_bucket, args.destination_bucket, LAMBDA_CODE_BUCKET, stack_exists)

    wait_for_stack_creation_or_update(args.stack_name, stack_exists, skip_waiting)

    upload_file_to_s3(args.test_file, args.source_bucket, os.path.basename(args.test_file), args.region)

if __name__ == "__main__":
    main()
