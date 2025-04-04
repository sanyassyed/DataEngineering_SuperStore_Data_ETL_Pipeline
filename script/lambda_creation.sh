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
conda activate .venv/
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
# Got size error so removed unnecessary packages; look at project creation for details

# created function in the wrong region
# aws lambda delete-function --function-name superstore

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

# add the event notification s3_file_upload to the s3 object
aws s3api put-bucket-notification-configuration --bucket wcd-week3-lambda-miniproject --notification-configuration file://notification.json

# test the function on the aws console
# if errors in code; fix the errors locally
# add updated lambd_function.py to .zip file
zip -g superstore.zip lambda_function.py
# update the function on aws
aws lambda update-function-code --function-name superstore --zip-file fileb://superstore.zip

# TEST
# Turn on the DB in RDS
# upload the file from local system to s3
cd /home/ubuntu/DataEngineering_SuperStore_Data_ETL_Pipeline
conda activate
# Run the script to pull top 10 customer ID's from RDS and write the .json file to s3 bucket input folder
bash script/run.sh

# This should push .json file to s3 and that inturn should trigger the Lambda function

# Errors - Not Required but keep in mind
# Turn on Database
# The sql libraries packaged don't work on lambda so going to change just those in the .zip file
# these packages are required only for lambda and not the local system
# first we need to remove the older version and then install the new versions
# Remove SQLAlchemy-2.0.37.dist-info and mysql_connector-2.2.9.dist-info and replace with mysql-connector-python==8.0.33 and sqlalchemy==2.0.37?
unzip superstore.zip -d clean_build
rm -rf clean_build/mysql_connector-2.2.9.dist-info clean_build/SQLAlchemy-2.0.37.dist-info
pip install mysql-connector-python==8.0.33 -t clean_build
pip install SQLAlchemy==2.0.37 -t clean_build
cd clean_build
zip -r ../superstore.zip .
cd ..
unzip -l superstore.zip
