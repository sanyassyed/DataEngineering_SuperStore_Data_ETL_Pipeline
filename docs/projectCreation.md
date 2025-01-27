# ETL Pipeline using Lambda

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

## Installing apps required
* NOTE: EC2 instance comes with python 3.10 installed but we wont be using it
```bash 
which python3
python3 --version
```
* installing miniconda followed by python 3.12 and pip
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
