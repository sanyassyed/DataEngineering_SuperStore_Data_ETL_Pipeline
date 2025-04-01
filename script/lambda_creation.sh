# Install zip
sudo apt install zip -y
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
zip -r9 superstore.zip aws_utils
# Add the lambda_function to the .zip file
zip -g superstore.zip lambda_function.py
# Add the script/.env file with environment variables to the .zip file
zip -g superstore.zip .env
# check the contents of the zip file as follows
unzip -l superstore.zip

# goto the folder with the package
cd ${thisfolder}

# Create the Lambda Role and attach policy
aws iam create-role --role-name superstore_lambda_role --assume-role-policy-document '{"Version": "2012-10-17","Statement": [{ "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'

# Policy 1
aws iam attach-role-policy --role-name superstore_lambda_role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
# Policy 2
aws iam attach-role-policy --role-name superstore_lambda_role --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# Create the lambda function
aws lambda create-function --function-name superstore --zip-file fileb://superstore.zip --handler lambda_function.lambda_handler --runtime python3.12 --role arn:aws:iam::209479284263:role/superstore_lambda_role