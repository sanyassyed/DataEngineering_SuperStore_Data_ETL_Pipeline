import os
import logging
import toml
import json
from sqlalchemy import create_engine, text
import requests
from dotenv import load_dotenv
import boto3
from typing import Tuple, Optional
from urllib.parse import unquote_plus

load_dotenv()
# Load environment variables
# Database credentials
HOST_MYSQL = os.getenv('HOST_MYSQL')
USER = os.getenv('USER_MYSQL')
PASSWORD = os.getenv('PASSWORD')
DB_NAME = os.getenv('DATABASE')
PORT = os.getenv('PORT')
URL = os.getenv('URL')



# Configure Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# we have already givem Lambda IAM permission to access s3 bucket so we do not need to give access keys
s3_client = boto3.client('s3')


def connect_db():
    """
    Establishes a connection to the specified database and returns the connection engine.
    
    Args:
    db_name (str): Name of the database hosted on AWS RDS.

    Returns:
    sqlalchemy.engine.base.Engine: Database connection engine.
    """
    connection_string = f"mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST_MYSQL}:{PORT}/{DB_NAME}"
    try:
        engine = create_engine(connection_string, echo=True)
        logger.info(f"Connected to the Database")
    except Exception as e:
        print(f"Something went wrong: {e}")
        print("Could not connect to the database")
        return None
    return engine

def disconnect_db(engine):
    """
    Closes the database connection.

    Args:
    engine (sqlalchemy.engine.base.Engine): Active database connection engine.
    """
    engine.dispose()
    logger.info("Database connection closed")
    return None


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
    logger.info(f"Extracted customer ids from json file as {ids_str}")
    return ids_str

def extract_names_db(engine, ids_str):
    logger.info("Querying the orders table to extract names")
    query = text(f"SELECT CustomerID, CustomerName, CURDATE() AS 'date' FROM customers WHERE CustomerID IN {ids_str} ORDER BY CustomerID ASC")
    try:
        # Execute the query with parameters
        with engine.connect() as conn:
            result = conn.execute(query)
        logger.info(f"Data extracted from db")
        result_l = []
        for r in result:
            result_l.append({"id":r[0], "name":r[1], "date":str(r[2])})
        return result_l
    except Exception as e:
        logger.error(f"Following error when running query on the database: {e}")
    return None


def post_api(result, url):
    logger.info(f"Posting the following data to API: {result}")
    response = requests.post(url, data = json.dumps(result))
    return response



def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])

    logger.info(f"The key/file uploaded is: {key}")

    ids_str = extract_ids(bucket, key)

    if not ids_str:
        logger.error("Failed to extract customer IDs from JSON file.")
        return

    engine = connect_db()
    if engine is not None:
        result = extract_names_db(engine, ids_str)
        disconnect_db(engine)
        
        if result is not None:
            response = post_api(result, URL)
            if response.status_code == 201:
                logger.info("SUCCESS: Data posted to API")
            else:
                logger.error(f"Request failed: {response.status_code} - {response.text}")
        else:
            logger.error("ERROR: Could not extract names from the DB")
    else:
        logger.error("ERROR: Could not establish DB connection")