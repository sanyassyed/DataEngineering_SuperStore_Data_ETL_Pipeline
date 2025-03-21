import boto3
import os
import logging
from dotenv import load_dotenv
from typing import Tuple, Optional
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

AWS_ACCESS_KEY = os.getenv('ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('SECRET_KEY')

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

def connect_db(db_name, user, password, host_mysql):
    """
    Establishes a connection to the specified database and returns the connection engine.
    
    Args:
    db_name (str): Name of the database hosted on AWS RDS.

    Returns:
    sqlalchemy.engine.base.Engine: Database connection engine.
    """
    connection_string = f"mysql+mysqlconnector://{user}:{password}@{host_mysql}:3306/{db_name}"
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