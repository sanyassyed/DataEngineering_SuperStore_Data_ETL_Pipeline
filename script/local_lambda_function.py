import os
import sys
import logging
import argparse
import toml
import json
from sqlalchemy import text
import requests
from dotenv import load_dotenv
from aws_utils.aws_utils import connect_to_s3, connect_db, disconnect_db

load_dotenv()
# Load environment variables

# Database credentials
HOST_MYSQL = os.getenv('HOST_MYSQL')
USER = os.getenv('USER_MYSQL')
PASSWORD = os.getenv('PASSWORD')

# Project Directories
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER')
LOG_FILE = os.getenv('LOG_FILE_PYTHON')

# Configure Logging
logging.basicConfig(
                    level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s : %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    filename=LOG_FILE,
                   )


def extract_ids(bucket_name, file_path_s3):
    """
    Extract the customer ids by:
    1. Connecting to S3
    2. Pulling the json file from the s3 bucket as a python dictionary using json
    3. Reading the ids from the dictionary as strings

    Args:
    bucket_name (str): Name of the s3 bucket
    file_path_s3 (str): The json file name along with the entire path to the file on s3

    Returns:
    str: A string of customer ids

    """
    s3, s3_client = connect_to_s3()
    # Get the file inside the S3 Bucket
    s3_response = s3_client.get_object(Bucket=bucket_name, Key=file_path_s3)

    # Get the Body object in the S3 get_object() response
    s3_object_body = s3_response.get('Body')

    # Read the data in bytes format
    content = s3_object_body.read()

    # extract customer_id from the json file as dict
    json_dict = json.loads(content)
    
    # extract the customer ids as a list
    ids_str = "(" + ", ".join([str(x) for x in json_dict['CustomerID'].values()]) + ")"
    logging.info(f"Extracted customer ids from json file as {ids_str}")
    return ids_str

def extract_names_db(engine, ids_str):
    logging.info("Querying the orders table to extract names")
    query = text(f"SELECT CustomerID, CustomerName, CURDATE() AS 'date' FROM customers WHERE CustomerID IN {ids_str} ORDER BY CustomerID ASC")
    try:
        # Execute the query with parameters
        with engine.connect() as conn:
            result = conn.execute(query)
        logging.info(f"Data extracted from db")
        result_l = []
        for r in result:
            result_l.append({"id":r[0], "name":r[1], "date":str(r[2])})
        return result_l
    except Exception as e:
        logging.error(f"Following error when running query on the database: {e}")
    return None


def post_api(result, url):
    logging.info("Posting data to API")
    logging.info(result)
    response = requests.post(url, data = json.dumps(result))
    return response

def main():
    # Getting Config
    # DB
    app_config = toml.load('config.toml')
    db_name = app_config['mysql']['database']
    url = app_config['api']['url']

    # AWS
    bucket_name = app_config['aws']['bucket_name']
    file_path_s3 = app_config['aws']['file_path_s3']

    # Download json from s3 & extract the customer ids from the file
    ids_str = extract_ids(bucket_name, file_path_s3)
    
    engine = connect_db(db_name, USER, PASSWORD, HOST_MYSQL)
    if engine is not None:
        result = extract_names_db(engine, ids_str)
        disconnect_db(engine)
        if result is not None:
            response = post_api(result, url)
            if response.status_code == 201:
                logging.info(f"Data posted to the API: {result}")
                logging.info("Request successful: data posted!")
                logging.info("SUCCESS: Code executed successfully to post data to API; TERMINATING code")
            else:
                logging.error(f"Request failed with status code {response.status_code}")
                logging.error(response.text)
        else:
            logging.error("ERROR: Could not extract names for the DB; TERMINATING code")
    else:
        logging.error("ERROR: Could not establish DB connection; TERMINATING code")



if __name__ == "__main__":
    main()

