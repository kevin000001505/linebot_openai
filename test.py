import logging, os
import psycopg2
from worker.celery_worker import fetch_stock_news
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def check_redis_connection():
    try:
        # Attempt to connect to Redis
        r = redis.Redis(host='red-csne29aj1k6c73b1t0g0', port=6379, db=0)
        r.ping()  # This will raise an exception if the connection fails
        logger.info("Successfully connected to Redis.")
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")

def test_postgresql_connection():
    try:
        # Establish connection to PostgreSQL
        connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port='5432'
        )
        cursor = connection.cursor()

        # Execute a simple query to check the connection
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        logger.info(f"Successfully connected to PostgreSQL. Database version: {db_version}")

    except psycopg2.OperationalError as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
    finally:
        # Close the connection if it was established
        if 'connection' in locals() and connection:
            cursor.close()
            connection.close()
            logger.info("PostgreSQL connection closed.")

# Example usage
if __name__ == "__main__":
    # Check Redis connection
    # check_redis_connection()

    # You can get stock_id from command line arguments or any other source
    stock_id = "2330"  # Example stock ID
    # fetch_stock_news(stock_id)
    test_postgresql_connection()
    # run_spiders(stock_id)