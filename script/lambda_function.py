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
AWS_ACCESS_KEY = os.getenv('ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('SECRET_KEY')
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

s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

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
        logger.info(f"Connected to the Database: {engine}")
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
    logger.info(f"connected to s3 {s3_client}")
    #s3_client.download_file(Bucket=bucket_name, Key=file_path_s3)
    # Get the file inside the S3 Bucket
    logger.info("getting the response from s3")
    s3_response = s3_client.get_object(Bucket=bucket_name, Key=file_path_s3)
    logger.info(f"response received from s3 {s3_response}")
    logger.info("getting the body from s3 response")
    # Get the Body object in the S3 get_object() response
    s3_object_body = s3_response.get('Body')
    logger.info("getting the content from s3 response")
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
    logger.info(f"Query is {query}")
    # Execute the query with parameters
    with engine.connect() as conn:
        logger.info("tring to connect to db.......")
        result = conn.execute(query)
    logger.info(f"Data extracted from db")
    result_l = []
    for r in result:
        result_l.append({"id":r[0], "name":r[1], "date":str(r[2])})
    return result_l



def post_api(result, url):
    logger.info("Posting data to API")
    logger.info(result)
    response = requests.post(url, data = json.dumps(result))
    return response

def test_connection(engine):
    try:
        with engine.connect() as conn:
            logger.info("Connected successfully")
            result = conn.execute(text("SELECT 1"))
            logger.info(f"Test query result: {result.fetchall()}")
    except Exception as e:
        logger.error(f"Test DB connection failed: {e}")

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])

    logger.info(f"The key/file uploaded is: {key}")
    logger.info(f"The bucket name is: {bucket}")



    logger.info(f"Calling function to extract ids from uploaded json file")

    #logger.info(f"Keys: AWS_ACCESS_KEY = {AWS_ACCESS_KEY} AWS_SECRET_KEY = {AWS_SECRET_KEY} HOST_MYSQL = {HOST_MYSQL} USER = {USER} PASSWORD = {PASSWORD} DB_NAME = {DB_NAME} PORT = {PORT} URL = {URL}")

    ids_str = extract_ids(bucket, key)
    logger.info(f"Ids Extracted as follows: {ids_str}")

    
    if not ids_str:
        logger.error("Failed to extract customer IDs from JSON file.")
        return

    logger.info("connecting to db")
    engine = connect_db()

    if engine is not None:
        logger.info("Connected to the database")
        #test_connection(engine)
        result = extract_names_db(engine, ids_str)
        logger.info(f"Data extracted from db: {result}")
        disconnect_db(engine)
        
        if result is not None:
            logger.info("Posting data to API")
            response = post_api(result, URL)
            if response.status_code == 201:
                logger.info("SUCCESS: Data posted to API")
            else:
                logger.error(f"Request failed: {response.status_code} - {response.text}")
        else:
            logger.error("ERROR: Could not extract names from the DB")
    else:
        logger.error("ERROR: Could not establish DB connection")

