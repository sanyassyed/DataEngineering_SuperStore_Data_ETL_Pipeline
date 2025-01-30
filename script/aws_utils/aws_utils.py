import boto3
import os
import logging
from dotenv import load_dotenv
from typing import Tuple, Optional

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