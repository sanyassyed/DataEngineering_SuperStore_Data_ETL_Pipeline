# Goto the folder with the python virtual env for the lambda function
cd /home/ubuntu/DataEngineering_SuperStore_Data_ETL_Pipeline/script
thisfolder=$(pwd)
# Goto the path with the dependencies
cd $thisfolder/.venv/lib/python3.12/site-packages
# Zip the dependencies into a zip file called superstore.zip and save in the script folder
zip -r9 ${thisfolder}/superstore.zip .
# Goto the script folder
cd ${thisfolder}
# Add the custom function in the folder aws_utils to the .zip folder
# zip -r9 superstore.zip aws_utils
# Remove the custom function folder aws_utils from the .zip folder
# zip -d superstore.zip 'aws_utils/*'
# Remove setuptools package from the .zip folder as it is already available on Lambda
zip -d superstore.zip 'setuptools/*'

# Add the lambda_function to the .zip file
zip -g superstore.zip lambda_function.py
# Add the script/.env file with environment variables to the .zip file
zip -g superstore.zip .env
# check the contents of the zip file as follows
unzip -l superstore.zip

# goto the folder with the package
cd ${thisfolder}

# aws is installed in the virtual folder of the project to go there
cd /home/ubuntu/DataEngineering_SuperStore_Data_ETL_Pipeline/
conda activate .venv
# configure aws
aws configure
# use the access key & secret key in .env file
# region us-east-2
# Default output format : Just Enter to ignore it
# add the following persmissions to the User Group "developers" 
# 1. CustomCreateRole: which allows this user to create the roles (Refer to projectCreation documentation to do this `Create custom Policy`)
# 2. AttachRolePolicy: to attach policies to the roles created
# 


# Create the Lambda Role and attach policy
aws iam create-role --role-name superstore_lambda_role --assume-role-policy-document '{"Version": "2012-10-17","Statement": [{ "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'

# make a note of the role's arn eg: arn:aws:iam::209479284263:role/superstore_lambda_role
# Policy 1
aws iam attach-role-policy --role-name superstore_lambda_role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
# Policy 2
aws iam attach-role-policy --role-name superstore_lambda_role --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# Create the lambda function
cd script
aws lambda create-function --function-name superstore --zip-file fileb://superstore.zip --handler lambda_function.lambda_handler --runtime python3.12 --role arn:aws:iam::209479284263:role/superstore_lambda_role
# Got size error; look at project creation for details


# bucket name : wcd-week3-lambda-miniproject
# folder with data: `input`
# Set the permission for Lambda to explicitly allow s3 to access the bucket
aws lambda add-permission \
  --function-name superstore \
  --statement-id AllowS3Invoke \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::wcd-week3-lambda-miniproject \
  --source-account 209479284263

# Create Event Notification for the s3 bucket which is usually set via the Console. This configuration needs to be saved to a notification.json file. TIP: To get the configuration of another such event to copy and paste then use the following command `aws s3api get-bucket-notification-configuration --bucket bucket_name --region us-east-2`  
cd /home/ubuntu/DataEngineering_SuperStore_Data_ETL_Pipeline/script
nano notification.json

