
aws cloudformation create-stack --stack-name copyStack1 --template-body file://copyTemplate.yaml --capabilities CAPABILITY_IAM --parameters ParameterKey=SourceBucketName,ParameterValue=your-source-bucket-name-12345 ParameterKey=DestinationBucketName,ParameterValue=your-destination-bucket-name-12345 ParameterKey=LambdaCodeBucketName,ParameterValue=copylambdafuncbucket 

aws cloudformation update-stack --stack-name copyStack1 --template-body file://copyTemplate.yaml --capabilities CAPABILITY_IAM --parameters ParameterKey=SourceBucketName,ParameterValue=your-source-bucket-name-12345 ParameterKey=DestinationBucketName,ParameterValue=your-destination-bucket-name-12345 ParameterKey=LambdaCodeBucketName,ParameterValue=copylambdafuncbucket  

aws s3 cp "C:\Users\anushka.yadav02\Documents\VSCODE\Training-py\Files\Salary.txt" s3://my-source-bucket-name-12345/ --region ap-south-1 

deploy - python script.py --lambda-directory lambda.py --zip-file-path lambda.zip --lambda-code-bucket copylambdafuncbucket --zip-file-key lambda.zip --region ap-south-1 --stack-name copyStack2 --template copyTemplate.yaml --source-bucket my-source-bucket-name-12345 --destination-bucket my-destination-bucket-name-12345 --test-file "C:\Users\anushka.yadav02\Documents\VSCODE\Training-py\Files\Salary.txt"
