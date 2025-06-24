# ETL Pipeline using Lambda

---

## System Specification
* Using EC2 instance from AWS
* System info: micro instance with Ubuntu 22.04
```bash
cat /etc/os-release
NPRETTY_NAME="Ubuntu 22.04.5 LTS"
NAME="Ubuntu"
VERSION_ID="22.04"
VERSION="22.04.5 LTS (Jammy Jellyfish)"
VERSION_CODENAME=jammy
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=jammy
```
* Security Group:
    * Inbound: 
        * Type: SSH
        * Protocol: TCP
        * Port Range: 22
        * Source type: My IP
    * Outbound
        * IPV4:
            * Type: All Traffic
            * Protocol: All
            * Port Range: All
            * Source type: All IPv4
        * IPV6:
            * Type: All Traffic
            * Protocol: All
            * Port Range: All
            * Source type: All IPv6

---

## Connecting to GitHub
* Create a project repo on gitHub called `DataEngineering_SuperStore_Data_ETL_Pipeline`
* Generate a SSH key on EC2 instance and add public key to gitHub
* Create a config file and add the config parameters to connect to gitHub via SSH
* Check SSH connection to gitHub
* Clone the repo from gitHub to EC2 instance
```bash
# generate a ssh key pair 
ssh-keygen -t rsa
# keys created here: /home/ubuntu/.ssh/id_rsa
cat /home/ubuntu/.ssh/id_rsa.pub 
# Add the public key to gitHub

# Create config file
cd /home/ubuntu/.ssh
nano config
# Add the below
Host github
        HostName github.com
        User git
        IdentityFile /home/ubuntu/.ssh/id_rsa

# Check connection to gitHub via SSH
ssh -vvv -T git@github.com

# Clone the remote project repo to the instance via ssh
git clone git@github.com:sanyassyed/DataEngineering_SuperStore_Data_ETL_Pipeline.git

# check the remote origin setting
git remote -v
# check git config
git config -l
git config --list --global
git config --global user.name
git config --global user.email

# set global username and email
git config --global user.name "ubuntu"
git config --global user.email "ubuntu@superstore.com"

# commit changes
git add .
git commit -m "ADD:Initial commit"
git push -u origin main
```

---

## Development Environment Setup 

### EC2 Instance 
* NOTE: EC2 instance comes with python 3.10 installed but we wont be using it
```bash 
which python3
python3 --version
```
* Miniconda
* python 3.12
* pip
* Virtual env
```bash
cd "${HOME}"
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
# -b (Batch mode):This option tells the installer to run in batch mode. In batch mode, the installer does not prompt for user input and will automatically proceed with the default installation settings.
# -p ${HOME}/miniconda:-p: This option specifies the installation path for Miniconda, i.e it will be installed in the folder miniconda.
bash ~/miniconda.sh -b -p ${HOME}/miniconda
rm ~/miniconda.sh
eval "$(~/miniconda/bin/conda shell.bash hook)" && conda init
source ~/.bashrc
# now you should see (base) appear


# Create virtual env in the project folder
cd DataEngineering_SuperStore_Data_ETL_Pipeline 
conda create --prefix ./.venv python=3.12 pip -y
# activate the virtual env
conda activate ./venv
# check python version
which python
python --version
```
* zip
```bash
# install zip
sudo apt install -y zip unzip
```
* aws
Install the aws via python in the virtual env
```bash
cd /home/ubuntu/DataEngineering_SuperStore_Data_ETL_Pipeline
conda activate .venv
# check if already installed
aws --version
# if command not found install aws along with other dependencies with versions that are compatable using the following command
pip install --upgrade awscli boto3 botocore s3transfer urllib3 six
```
---

### DATABASE
* Goto RDS on AWS
#### RDS
* Select the options mentioned below [Source](https://www.youtube.com/watch?v=Ng_zi11N4_c)
* Standard Create
* Engine Options: MySql
* Edition: MySql Community
* Engine Version: MySWL 8.0.40
* Templates: Free tier
* Availability: Not available for free tier
* Settings: `superstore-database` any custom name you like
* Credentails settings: 
	* Master username: admin 
	* Credentials Management: Self managed
	* Master Password: p******** 
* Instance Configuration: 
	* Burstable classes
	* db.t3.micro
* Storage:
	* Storage Type: General Purpose SSD
	* Allocated Storage: 20
	* Additional storage configuration: Enable storage autoscaling
	* Maximum storage threshold: 1000
* Connectivity: 
	* Compute Reaource - Don't connect
		* VPC: default
		* DB subnet group: default
		* Public Access: Yes
		* VPC security group: Choose existing
		* Existing VPC security groups: default
		* Availability Zone: No preference
	* Additional configuration: Database port- 3306
* Database authentication - password authentication
* Additional configuration: leave default settings
* Everything else leave as default
* Select `Create Database` button
* Goto the security group of the database
* In the inbound rules add 2 more rules `All Traffic` for
	* Ipv4
	* Ipv6
---
### MySql Workbench
* Click in the + symbol
* Connection Name: `superstore` (or any name you like)
* Connection Method: TCP/IP
* Hostname: Paste the Enpoint copied from AWS RDS console here
* Username: admin (same as above)
* Test Connection
* OK
* The connection will then appear in the home page
* Click on the connection
* Add the password when prompted
* Run the [sql script]() to load the dataset
* Write the query to extract top 10 customers with maximum sales

## Data Extraction
* Steps to perform via the EC2 instance
	* Query the `superstore` DB on RDS
	* Extract the top 10 customers by Sales
	* Save the results as Json on EC2 instance
	* Upload the json file to S3 bucket
* The scipt to perform this task is in the folder [script](../script/)
* To run the code to extract the top10 cutomers and store the result as a json file in the [output folder](../output/) run the following code from the project folder:
```bash
cd /home/ubuntu/DataEngineering_SuperStore_Data_ETL_Pipeline
bash script/run.sh
```
* The above code does the following
	1. Queries the `orders` table from AWS RDS and gets the customer id and sales of the top 10 customers
	1. Writes this data in the json format to the local system in the output folder
	1. Uploads this file from the output folder to the S3 bucket on AWS
* Once you run the script the top 10 customer data should be available in two locations- 
	1. Output folder contains the data in a .json file 
	2. S3 bucket `wcd-week3-lambda-miniproject`'s `/input` folder contains the same .json file
* This is the file which when uploaded to S3 should trigger the Lambda function
 
## Lambda
### Creating & Testing Function Locally
* ~~Create a folder `lambda` to store all lambda related files~~ This is not done as we are unable to use the aws_utils user defined functions
* Create another virtual env for the lambda function `.venv` in the script folder. You will use this folder to package the Lambda dependencies
* Write & Test the function locally - `local_lambda_function.py` as follows
```bash
cd /home/ubuntu/DataEngineering_SuperStore_Data_ETL_Pipeline
bash lambda/lambda_creation.sh
```
* The above will test the lambda locally by doing the following:
	1. Pull the customer Id's from the local json file in the output folder (In AWS Lambda; it will pull the same file from the the S3 bucket)
	1. Optionally you can do the same by pulling the data directly from S3 rather than the opuput folder (V2)
	1. Use the ID's and query `customer` table from AWS RDS and pull the customer names 
	1. Then POST this data in the json format to the API end point 
* Configure the function to include event_handler() - `lambda_function.py`
* Package the function and the dependencies `superstore_lambda.zip`
* Add the lambda_function.py to the .zip folder
```bash
# Create virtual env .venv for lambda function
cd lambda 
conda create --prefix ./.venv python=3.12 pip -y
# activate the virtual env
conda activate ./venv
# check python version
which python
python --version


```
### Creating function via AWS CLI
* Create a role for the lambda function: `superstore_role`
* Attach policies to the role	
	* LambdaBasicExecutionRole
	* S3FullAccess
* Create the lambda function on AWS
* Set permissions on Lambda to allow s3 to access it

### Create `Event Notification` on the s3 bucket 
* Write the notification configuration in the file `notification.json`
* Add the notification to the bucket which should trigger the lambda function 

### Create a Custom Policy As Follows:
* To attach a "create role" policy to a user group in AWS IAM, you need to create a policy that grants the group permissions to create roles, and then attach that policy to the group
* Navigate to IAM: Go to the AWS Management Console and navigate to the IAM service.
* Create Policy: Click on "Policies" in the navigation pane and then click "Create policy".
* Choose JSON: Select the JSON tab and paste the following policy document: 
* Code:
```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "iam:CreateRole"
                ],
                "Resource": "*"
            }
        ]
    }
```
* Now attach this policy to the user group developers



## Useful Links
* Connect to EC2 Instance via `EC2 Instance Connect` 
	* [Tutorial](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-tutorial.html#eic-tut1-task2)
	* First add the prefix list for EC2 instance connect to the security group Inbound Rule
	* Then Conncet to the instance via EC2 Instance Connect
* Reading data from s3 via boto 
	* [Blog](https://www.radishlogic.com/aws/how-to-load-a-json-file-from-s3-to-a-python-dictionary-using-boto3/#google_vignette)

## ERRORS:
* The awscli, boto3, botocore, s3transfer, urllib3, six all had conflicting versions so had to uninstall them all and reinstall versions compatable with each other.
* Lambda functions size error:
	* The.zip file was too large and has to be smaller than 70167211; mine was bigger
	* Solution: 
		1. ~~going to put the custom functions in aws_utils into the same lambda_function.py file ~~
		2. Deleted unnecessary packages like pandas
		3. Only add packages that are not available on Lambda. Adding all the packages in the virtual folder makes the size of the .zip file very large
* Within lambda s3 boto connection should be outside any function. It should be done right after the import statements and we don't need to give credentials as the lamda function already has the permission set for accessing s3 buckets
* DB was not turned on


## TODO: 
* Redo the steps for function creation in the right region
* Notes on when configuring aws cli we have to give permissions to the User to 1) create roles and 2) attach policies to these roles.
* These permissions will have to be given by creating custom policies
