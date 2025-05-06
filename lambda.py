import os
import boto3

s3 = boto3.client('s3')
SRC_BUCKET = os.environ['SOURCE_BUCKET']
DEST_BUCKET = os.environ['DEST_BUCKET']

def lambda_handler(event, context):
    for record in event['Records']:
        key = record['s3']['object']['key']
        print(f"Copying {key} from {SRC_BUCKET} to {DEST_BUCKET}")
        s3.copy_object(Bucket=DEST_BUCKET, CopySource={'Bucket': SRC_BUCKET, 'Key': key}, Key=key)
    return {'status': 'copied'}