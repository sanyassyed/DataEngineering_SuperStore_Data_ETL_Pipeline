import os
import sys
import logging
import argparse
import toml
import json
from sqlalchemy import create_engine, text
import requests
from dotenv import load_dotenv

load_dotenv()
# loading env variables
HOST_MYSQL = os.getenv('HOST_MYSQL')
USER = os.getenv('USER_MYSQL')
PASSWORD = os.getenv('PASSWORD')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def connect_db(db_name):
    connection_string = f"mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST_MYSQL}:3306/{db_name}"
    try:
        engine = create_engine(connection_string, echo=True)
        logger.info(f"Connected to the Database")
    except Exception as e:
        logger.error(f"Something went wrong: {e}")
        logger.error("Could not connect to the database")
        return None
    return engine

def disconnect_db(engine):
    engine.dispose()
    logger.info("Database connection closed")
    return None

def extract_ids_json(input_data_path):
    # extract customer_id from the json file
    with open(os.path.join(OUTPUT_FOLDER, input_data_path), 'r') as f:
        data_json = json.load(f)
    # extract the customer ids as a list
    ids_str = "(" + ", ".join([str(x) for x in data_json['CustomerID'].values()]) + ")"
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
    logger.info("Posting data to API")
    logger.info(result)
    response = requests.post(url, data = json.dumps(result))
    return response

def main():
    parser = argparse.ArgumentParser()
    # Set the default for the dataset argument
    parser.add_argument("--input_data")
    args = parser.parse_args()

    app_config = toml.load('config.toml')
    db_name = app_config['mysql']['database']
    url = app_config['api']['url']

    # Create a dictionary of the shell arguments
    ids_str = extract_ids_json(args.input_data)
    
    engine = connect_db(db_name)
    if engine is not None:
        result = extract_names_db(engine, ids_str)
        disconnect_db(engine)
        if result is not None:
            response = post_api(result, url)
            if response.status_code == 201:
                logger.info("Request successful: data posted!")
                logger.info("SUCCESS: Code executed successfully to post data to API; TERMINATING code")
            else:
                logger.error(f"Request failed with status code {response.status_code}")
                logger.error(response.text)
        else:
            logger.error("ERROR: Could not extract names for the DB; TERMINATING code")
    else:
        logger.error("ERROR: Could not establish DB connection; TERMINATING code")



if __name__ == "__main__":
    main()

