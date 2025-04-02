import os
import logging
import toml
import json
from sqlalchemy import create_engine, text
import requests
from dotenv import load_dotenv
import boto3
from typing import Tuple, Optional


load_dotenv()
# Load environment variables
AWS_ACCESS_KEY = os.getenv('ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('SECRET_KEY')
# Database credentials
HOST_MYSQL = os.getenv('HOST_MYSQL')
USER = os.getenv('USER_MYSQL')
PASSWORD = os.getenv('PASSWORD')
DB_NAME = os.getenv('DB_NAME')
PORT = os.getenv('PORT')
URL = os.getenv('URL')



# Configure Logging
logging.basicConfig(
                    level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s : %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                   )

def connect_to_s3() -> Tuple[Optional[boto3.resources.base.ServiceResource], Optional[boto3.client]]:
    """
    Establish a connection to AWS S3 using credentials from environment variables.

    Returns:
        tuple: s3 resource and s3 client objects.
    """
    logging.info("Initializing S3 connection...")
    try:
        session = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )
        s3 = session.resource('s3')
        s3_client = session.client('s3')
        logging.info("Connected to S3 successfully.")
        return s3, s3_client
    except Exception as e:
        logging.error(f"Failed to connect to S3: {e}")
        return None, None

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
        logging.info(f"Connected to the Database")
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
    logging.info("Database connection closed")
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



def lambda_handler(event, context):
	for record in event['Records']:
		bucket = record['s3']['bucket']['name']
		key = unquote_plus(record['s3']['object']['key'])

	logger.info(f"The key/file uploaded is: {key}")

	# Download json from s3 & extract the customer ids from the file
    ids_str = extract_ids(bucket, key)
    
    engine = connect_db()
    if engine is not None:
        result = extract_names_db(engine, ids_str)
        disconnect_db(engine)
        if result is not None:
            response = post_api(result, URL)
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

