import logging
import os
import toml
from dotenv import load_dotenv
import time
import pandas as pd
from aws_utils.aws_utils import connect_to_s3, connect_db, disconnect_db


load_dotenv()

# Load environment variables
# Database credentials
HOST_MYSQL = os.getenv('HOST_MYSQL')
USER = os.getenv('USER_MYSQL')
PASSWORD = os.getenv('PASSWORD')

# Project directories
LOG_FILE = os.getenv('LOG_FILE_PYTHON')
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER')

# Configure logging
logging.basicConfig(
                    level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s : %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    filename=LOG_FILE,
                   )

logging.info(f"Log file for this script: {LOG_FILE}")


def extract(engine, output_file_name):
    """
    Executes a query to retrieve the top 10 customers based on total sales, 
    saves the results as a JSON file in the output directory.

    Args:
    engine (sqlalchemy.engine.base.Engine): Active database connection engine.
    output_file_name (str): Filename for the output JSON file.

    Returns:
    str: Path of the saved JSON file.
    """
    logging.info("Executing query on the orders table.")
    output_file = os.path.join(OUTPUT_FOLDER, output_file_name)
    if not os.path.exists(OUTPUT_FOLDER):
            logging.info(f"Creating output directory: {OUTPUT_FOLDER}")
            os.mkdir(OUTPUT_FOLDER)

    query = """SELECT CustomerID, SUM(Sales) AS TotalCustomerSales  
               FROM orders 
               GROUP BY CustomerID 
               ORDER BY TotalCustomerSales DESC 
               LIMIT 10"""
    
    try:
        df = pd.read_sql(query, con=engine)
        df.to_json(output_file, index=False)
        logging.info(f"Data successfully extracted and saved to {output_file}.")
        return output_file
    except pd.errors.DatabaseError as e:
        logging.error(f"Database query error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during query execution: {e}")
    
    return None


def save_to_s3(output_file_name : str, output_file_path: str, bucket_name : str, region : str ='us-east-2') -> None:
    """
    Uploads the extracted JSON data file to an S3 bucket. If the bucket does not exist, it will be created.
    
    Args:
    output_file_name (str): Name of the file to be stored in S3.
    output_file_path (str): Local path of the file to be uploaded.
    bucket_name (str): Name of the target S3 bucket.
    region (str): AWS region where the bucket is located (default: 'us-east-2').
    """
    # Establish connection to AWS S3 
    s3, s3_client = connect_to_s3()
    output_file_name_s3 = f'input/{output_file_name}'

    if s3 and s3_client:
        # Check if the bucket exists; if not, create it.
        if not s3.Bucket(bucket_name) in s3.buckets.all():
            logging.info(f"Bucket '{bucket_name}' does not exist. Creating it...")
            s3_client.create_bucket(
                                    Bucket=bucket_name,
                                    CreateBucketConfiguration={'LocationConstraint': region}
                                    )
            logging.info(f"Bucket '{bucket_name}' successfully created on S3.")

        logging.info(f"Uploading {output_file_name} to S3 bucket: {bucket_name} in region: {region}.")

        try:
            with open(output_file_path, "rb") as file_data: 
                s3_client.put_object(Bucket=bucket_name, Key=output_file_name_s3, Body=file_data)
            logging.info(f"{output_file_name} successfully uploaded to S3.")
        except Exception as e:
            logging.error(f"S3 upload failed: {e}")
        return
    else:
        logging.error("Failed to establish connection to S3.")
        return


def main():
    """
    Runs the ETL process:
    - Connects to the superstore database on AWS RDS.
    - Extracts the top 10 customers based on total sales and saves results locally.
    - Uploads the extracted data to an S3 bucket.
    """
    # Load database and AWS configurations from a config file
    app_config = toml.load('config.toml')
    db_name = app_config['mysql']['database']

    # AWS configuration
    aws_bucket_name = app_config['aws']['bucket_name']
    aws_region = app_config['aws']['region']

    # Generate filename for the extracted JSON file
    output_file_name = f"top_10_customers_{time.strftime('%Y%m%d-%H%M%S')}.json"

    # Establish database connection
    engine = connect_db(db_name, USER, PASSWORD, HOST_MYSQL)
    
    if engine is not None:
        # Extract data from the database and save locally
        output_file_path = extract(engine, output_file_name)
        disconnect_db(engine)

        # Upload the extracted data to S3
        save_to_s3(output_file_name, output_file_path, aws_bucket_name, aws_region)
        logging.info("ETL process completed successfully.")
    else:
        logging.error("Database connection failed. ETL process aborted.")

if __name__=="__main__":
    main()