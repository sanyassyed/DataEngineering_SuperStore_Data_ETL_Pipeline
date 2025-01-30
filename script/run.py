import mysql.connector
import logging
import os
import toml
from dotenv import load_dotenv
import time
import pandas as pd

load_dotenv()

# loading env variables
HOST_MYSQL = os.getenv('HOST_MYSQL')
USER = os.getenv('USER_MYSQL')
PASSWORD = os.getenv('PASSWORD')

LOG_FILE = os.getenv('LOG_FILE_PYTHON')
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER')

logging.basicConfig(
                    level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s : %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    filename=LOG_FILE,
                   )

logging.info(f"LOG FILE FOR THIS PYTHON SCRIPT IS AT: {LOG_FILE}")


def connect_db(mysql_db):
    try:
        conn = mysql.connector.connect(host=HOST_MYSQL, 
                                    user=USER, 
                                    password=PASSWORD, 
                                    database=mysql_db, 
                                    auth_plugin='mysql_native_password')
        logging.info(f"Connected to the Database")
    except mysql.connector.Error as e:
        logging.error(f"Something went wrong: {e}")
        logging.error("Could not connect to the database")
        return None
    return conn

def disconnect_db(conn):
    conn.commit()
    conn.close()
    logging.info("Database connection closed")
    return None

def extract(conn):
    logging.info("Querying the orders table")
    output_file_name = f"top_10_customers_{time.strftime('%Y%m%d-%H%M%S')}.csv"
    output_file = os.path.join(OUTPUT_FOLDER, output_file_name)
    if not os.path.exists(OUTPUT_FOLDER):
            logging.info(f"Creating output folder at: {OUTPUT_FOLDER}")
            os.mkdir(OUTPUT_FOLDER)

    query = f"SELECT CustomerID, SUM(OrderQuantity * ((UnitPrice * (1- Discount)) + ShippingCost)) order_total  FROM orders GROUP BY CustomerID ORDER BY 2 DESC LIMIT 10"
    
    try:
        df = pd.read_sql(query, conn)
        df.to_csv(output_file, encoding='utf-8-sig', index=False)
        logging.info(f"Data extracted from db & written to the file {output_file}")
    except pd.errors.DatabaseError as e:
        logging.error(f"Following error when running query on the database: {e}")
    except Error as e:
        logging.error(f"Following error when running query on the database: {e}")
    return

def main():
    app_config = toml.load('config.toml')
    mysql_db = app_config['mysql']['database']


    connection = connect_db(mysql_db)
    
    if connection is not None:
        extract(connection)
        disconnect_db(connection)
    
    else:
        logging.error("Could not connect to the Database, aborting !!")

if __name__=="__main__":
    main()