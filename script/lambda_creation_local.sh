#!/bin/bash

##############################################################
# Project Path
script_path="$(cd "$(dirname "$(dirname "${BASH_SOURCE:-$0}")")" && pwd)"
echo "[INFO:] PROJECT DIRECTORY: ${script_path}"

##############################################################
# Setting local date variable
log_date=$(date +"%d-%m-%Y-%H-%M-%S")

##############################################################
# Load environment variables from config.toml

SCRIPT_FOLDER_NAME=$(grep 'lambda_script_folder' config.toml | sed 's/.*=//' | tr -d '"')
OUTPUT_FOLDER_NAME=$(grep 'output_folder' config.toml | sed 's/.*=//' | tr -d '"')
LOG_FOLDER_NAME=$(grep 'log_folder' config.toml | sed 's/.*=//' | tr -d '"')
PYTHON_FILE_NAME=$(grep 'lambda_py_script' config.toml | sed 's/.*=//' | tr -d '"')
SCRIPT_FILE_NAME=$(grep 'lambda_sh_script' config.toml | sed 's/.*=//' | tr -d '"')
VIRTUAL_ENV_PATH=$(grep 'lambda_virtual_env_path' config.toml | sed 's/.*=//' | tr -d '"')

# Derived paths
PROJECT_FOLDER="${script_path}"
export OUTPUT_FOLDER="${PROJECT_FOLDER}/${OUTPUT_FOLDER_NAME}"
SCRIPT_FOLDER="${PROJECT_FOLDER}/${SCRIPT_FOLDER_NAME}"
PYTHON_FILE="${SCRIPT_FOLDER}/${PYTHON_FILE_NAME}"
SCRIPT_FILE="${SCRIPT_FOLDER}/${SCRIPT_FILE_NAME}"
LOG_FOLDER="${PROJECT_FOLDER}/${LOG_FOLDER_NAME}"
LOG_FILE_NAME="${SCRIPT_FILE_NAME}_${log_date}.log"
LOG_FILE_NAME_PYTHON="${PYTHON_FILE_NAME}_${log_date}.log"
LOG_FILE="${LOG_FOLDER}/${LOG_FILE_NAME}"
export LOG_FILE_PYTHON="${LOG_FOLDER}/${LOG_FILE_NAME_PYTHON}"

##############################################################
# Setting log rules
exec > >(tee ${LOG_FILE}) 2>&1

##############################################################
# Activating virtual environment
echo "[INFO:] Activating virtual env"
# Initialize Conda for the script
eval "$(conda shell.bash hook)"
conda activate ${VIRTUAL_ENV_PATH}

##############################################################
# Metadata
echo "[INFO:] Metadata:"
echo "[INFO:] Output data folder: ${OUTPUT_FOLDER}"
echo "[INFO:] Script file: ${SCRIPT_FILE}"
echo "[INFO:] Python file: ${PYTHON_FILE}"
echo "[INFO:] Log file for ${SCRIPT_FILE_NAME} at: ${LOG_FILE}"
echo "[INFO:] Log file for ${PYTHON_FILE_NAME} at: ${LOG_FILE_PYTHON}"

##############################################################
# Step 2: Running Python Script
echo "[INFO:] Running Python script at: ${PYTHON_FILE}"

# PRODUCTION MODE
echo "[INFO:] Running in Production Mode:"
python3 "${PYTHON_FILE}"

# TESTING MODE (uncomment if needed):
#echo "[INFO:] Running in Test Mode:"
#python3 "${PYTHON_FILE}" --test_run

RC1=$?
if [ ${RC1} != 0 ]; then
    echo "[DEBUG:] PYTHON RUNNING FAILED"
    echo "[ERROR:] RETURN CODE: ${RC1}"
    echo "[ERROR:] REFER TO THE LOG FOR THE REASON FOR THE FAILURE."
    exit 1
fi

echo "PYTHON PROGRAM RUN SUCCEEDED"

conda activate

exit 0

# Run this file as follows
# cd /home/ubuntu/DataEngineering_SuperStore_Data_ETL_Pipeline
# bash script/lambda_creation_local.sh
# NOTE: To change the file name/path to be downloaded from s3 do it in config.toml 