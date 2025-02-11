import os
import sys
import uuid
import argparse
from urllib.parse import unquote_plus
from PIL import Image
import PIL.Image
import json
from sqlalchemy import create_engine, text, bindparam

# loading env variables
HOST_MYSQL = os.getenv('HOST_MYSQL')
USER = os.getenv('USER_MYSQL')
PASSWORD = os.getenv('PASSWORD')


def connect_db(db_name):
    connection_string = f"mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST_MYSQL}:3306/{db_name}"
    try:
        engine = create_engine(connection_string, echo=True)
        logging.info(f"Connected to the Database")
    except Exception as e:
        print(f"Something went wrong: {e}")
        print("Could not connect to the database")
        return None
    return engine

def disconnect_db(engine):
    engine.dispose()
    logging.info("Database connection closed")
    return None


def extract_ids_json(input_data_path):
    # extract customer_id from the json file
    with open(input_data_path, 'r') as f:
        data_json = json.load(f)
    # extract the customer ids as a list
    customer_ids = list(data_json['CustomerID'].values())
    return customer_ids

def extract(engine, customer_ids):
    logging.info("Querying the orders table")

    query = "SELECT CustomerID, CustomerName, CURDATE() AS 'date' FROM customers WHERE CustomerID IN :customer_ids"
    stmt = text(query).bindparams(bindparam("customer_ids", type_=Int
eger, expanding=True))
    try:
        # Execute the query with parameters
        result = conn.execute(query %format_strings, tuple(customer_ids))
    
        logging.info(f"Data extracted from db & written to the file {output_file}")
        return output_file
    except pd.errors.DatabaseError as e:
        logging.error(f"Following error when running query on the database: {e}")
    except Exception as e:
        logging.error(f"Following error when running query on the database: {e}")
    
    return None
    
def main():
    parser = argparse.ArgumentParser()
    # Set the default for the dataset argument
    parser.add_argument("input_data")
    args = parser.parse_args()

    app_config = toml.load('config.toml')
    db_name = app_config['mysql']['database']

    # Create a dictionary of the shell arguments
    customer_ids = extract_ids_json(args.input_data)
    
    engine = connect_db(db_name)
    if engine is not None:
        result = extract_names_db(engine, customer_ids)
        disconnect_db(engine)

if __name__ == "__main__":
    main()