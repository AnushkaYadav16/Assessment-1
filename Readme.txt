
create/update stack => python script.py --lambda-file lambda.py --zip-file-key lambda.zip --region ap-south-1 --stack-name copyStack3 --template copyTemplate.yaml --source-bucket my-source-bucket-name-123345 --destination-bucket my-destination-bucket-name-123345 --test-file "C:\Users\anushka.yadav02\Documents\VSCODE\Training-py\Files\Salary.txt"

upload file => aws s3 cp "C:\Users\anushka.yadav02\Documents\VSCODE\Training-py\Files\Salary.txt" s3://my-source-bucket-name-12345/ --region ap-south-1 

delete stack => aws cloudformation delete-stack --stack-name copyStack3
