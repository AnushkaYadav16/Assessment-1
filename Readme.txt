
aws cloudformation create-stack --stack-name copyStack1 --template-body file://copyTemplate.yaml --capabilities CAPABILITY_IAM --parameters ParameterKey=SourceBucketName,ParameterValue=your-source-bucket-name-12345 ParameterKey=DestinationBucketName,ParameterValue=your-destination-bucket-name-12345 ParameterKey=LambdaCodeBucketName,ParameterValue=copylambdafuncbucket 

aws cloudformation update-stack --stack-name copyStack1 --template-body file://copyTemplate.yaml --capabilities CAPABILITY_IAM --parameters ParameterKey=SourceBucketName,ParameterValue=your-source-bucket-name-12345 ParameterKey=DestinationBucketName,ParameterValue=your-destination-bucket-name-12345 ParameterKey=LambdaCodeBucketName,ParameterValue=copylambdafuncbucket  

aws s3 cp "C:\Users\anushka.yadav02\Documents\VSCODE\Training-py\Files\Salary.txt" s3://my-source-bucket-name-12345/ --region ap-south-1 

deploy - python script.py --lambda-directory lambda.py --zip-file-path lambda.zip --lambda-code-bucket copylambdafuncbucket --zip-file-key lambda.zip --region ap-south-1 --stack-name copyStack3 --template copyTemplate.yaml --source-bucket my-source-bucket-name-123345 --destination-bucket my-destination-bucket-name-123345 --test-file "C:\Users\anushka.yadav02\Documents\VSCODE\Training-py\Files\Salary.txt"


python deploy_lambda_to_s3.py --lambda-directory /path/to/lambda/code --zip-file-path /path/to/output.zip --lambda-code-bucket your-lambda-code-bucket --zip-file-key lambda.zip --region us-east-1 --stack-name my-cloudformation-stack --template /path/to/cloudformation-template.yaml --source-bucket your-source-bucket  --destination-bucket your-destination-bucket --test-file /path/to/test-file.txt


create/update stack => python script.py --lambda-file lambda.py --zip-file-key lambda.zip --region ap-south-1 --stack-name copyStack3 --template copyTemplate.yaml --source-bucket my-source-bucket-name-123345 --destination-bucket my-destination-bucket-name-123345 --test-file "C:\Users\anushka.yadav02\Documents\VSCODE\Training-py\Files\Salary.txt"

upload file => aws s3 cp "C:\Users\anushka.yadav02\Documents\VSCODE\Training-py\Files\Salary.txt" s3://my-source-bucket-name-12345/ --region ap-south-1 

delete stack => aws cloudformation delete-stack --stack-name copyStack3
