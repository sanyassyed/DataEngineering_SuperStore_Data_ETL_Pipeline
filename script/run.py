from sqlalchemy import create_engine
import logging
import os
import toml
from dotenv import load_dotenv
import time
import pandas as pd
from aws_utils.aws_utils import connect_to_s3


load_dotenv()

# Loading env variables
# Database secrets
HOST_MYSQL = os.getenv('HOST_MYSQL')
USER = os.getenv('USER_MYSQL')
PASSWORD = os.getenv('PASSWORD')

# Project directories
LOG_FILE = os.getenv('LOG_FILE_PYTHON')
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER')

# Setting up logging
logging.basicConfig(
                    level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s : %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    filename=LOG_FILE,
                   )

logging.info(f"LOG FILE FOR THIS PYTHON SCRIPT IS AT: {LOG_FILE}")


def connect_db(db_name):
    """
    Connects to the DB db_name and returns the connection engine
    
    Args:
    db_name (str): The name of the database to connect to on AWS RDS

    Returns:
    sqlalchemy.engine.base.Engine: Connects to the db and returns the connection engine

    """
    connection_string = f"mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST_MYSQL}:3306/{db_name}"
    try:
        engine = create_engine(connection_string, echo=True)
        logging.info(f"Connected to the Database")
    except Exception as e:
        logging.error(f"Something went wrong: {e}")
        logging.error("Could not connect to the database")
        return None
    # print(f"This is what is returned: {type(engine)}")
    return engine

def disconnect_db(engine):
    """
    Disconnects from the db using the connection engine

    Args:
    engine (sqlalchemy.engine.base.Engine): The connection engine connected to the db

    """
    engine.dispose()
    logging.info("Database connection closed")
    return None

def extract(engine, output_file_name):
    """
    Uses the connection engine and extracts query result from the database using pandas 
    And stores the df as json data with output_file_name in the output folder

    Args:
    engine (sqlalchemy.engine.base.Engine): the connection engine with the db connection
    output_file_name (str): The name for the .json data file

    Returns:
    str: The path along with the name of the .json file where the output data is stored
    """
    logging.info("Querying the orders table")
    output_file = os.path.join(OUTPUT_FOLDER, output_file_name)
    if not os.path.exists(OUTPUT_FOLDER):
            logging.info(f"Creating output folder at: {OUTPUT_FOLDER}")
            os.mkdir(OUTPUT_FOLDER)

    query = f"SELECT CustomerID, SUM(Sales) TotalCustomerSales  FROM orders GROUP BY CustomerID ORDER BY 2 DESC LIMIT 10"
    
    try:
        df = pd.read_sql(query, con=engine)
        df.to_json(output_file, index=False)
        logging.info(f"Data extracted from db & written to the file {output_file}")
        return output_file
    except pd.errors.DatabaseError as e:
        logging.error(f"Following error when running query on the database: {e}")
    except Exception as e:
        logging.error(f"Following error when running query on the database: {e}")
    
    return None


def save_to_s3(output_file_name : str, output_file_path: str, bucket_name : str, region : str ='us-east-2') -> None:
    """
    Uploads a DataFrame to an S3 bucket as a Parquet file. Creates the S3 bucket if it doesn't exist.
    
    Args:
        df (pandas.DataFrame): The DataFrame to upload.
        output_file_name (str): The name of the file to be saved in S3.
        bucket_name (str): The name of the S3 bucket.
        region (str): The AWS region where the bucket is located (default: 'us-east-2').
    """
    # Establish a connection to AWS S3 
    s3, s3_client = connect_to_s3()
    output_file_name_s3 = f'input/{output_file_name}'

    if s3 and s3_client:
        # Check & create s3 bucket
        if not s3.Bucket(bucket_name) in s3.buckets.all():
            logging.info(f"{bucket_name} BUCKET DOES NOT EXIST IN S3; SO CREATING IT")
            s3_client.create_bucket(
                                    Bucket=bucket_name,
                                    CreateBucketConfiguration={'LocationConstraint':region}
                                    )
            logging.info(f"{bucket_name} BUCKET CREATED ON S3")


        logging.info(f"Uploading data to S3 bucket: {bucket_name} in region: {region}")

        try:
            with open(output_file_path, "rb") as file_data: 
                s3_client.put_object(Bucket=bucket_name, Key=output_file_name_s3, Body=file_data)
            logging.info(f"{output_file_name} DATA UPLOADED TO S3 AS PARQUET")
        except Exception as e:
            logging.error(f"DATA UPLOAD FAILED DUE TO: {e}")
        return
    else:
        logging.error("Could not connect to S3")
        return


def main():
    """
    Connects to superstore db on AWS RDS
    Pulls Top 10 customer data via query
    Store the results as json file locally in the output folder
    Uploads the json file to s3 bucket

    """
    # Extracting credentials from the config file
    # Database name
    app_config = toml.load('config.toml')
    db_name = app_config['mysql']['database']

    # AWS config
    aws_bucket_name = app_config['aws']['bucket_name']
    aws_region = app_config['aws']['region']

    # Setting json file name
    output_file_name = f"top_10_customers_{time.strftime('%Y%m%d-%H%M%S')}.json"

    # Connecting to DB
    engine = connect_db(db_name)
    
    if engine is not None:
        # Extracting data from DB and saving locally as a json file
        output_file_path = extract(engine, output_file_name)
        disconnect_db(engine)

        # Upload to S3
        # Uploading the json file to s3
        save_to_s3(output_file_name, output_file_path, aws_bucket_name, aws_region)
        logging.info(f"ETL Complete!")
    else:
        logging.error("Could not connect to the Database, aborting !!")

if __name__=="__main__":
    main()