#aws s3 cp C:\Users\anushka.yadav02\Documents\VSCODE\Training-py\Files\Salary.pdf s3://my-source-bucket-4243/

create stack - aws cloudformation create-stack --stack-name S3LambdaStack --template-body file://copyTemplate.yaml --capabilities CAPABILITY_IAM --parameters ParameterKey=SourceBucketName,ParameterValue=your-source-bucket-name-123 ParameterKey=DestinationBucketName,ParameterValue=your-destination-bucket-name-123

update stack - aws cloudformation update-stack --stack-name S3LambdaStack --template-body file://copyTemplate.yaml --capabilities CAPABILITY_IAM --parameters ParameterKey=SourceBucketName,ParameterValue=your-source-bucket-name-123 ParameterKey=DestinationBucketName,ParameterValue=your-destination-bucket-name-123






