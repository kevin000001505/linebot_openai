import logging
from worker.celery_worker import fetch_stock_news
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_redis_connection():
    try:
        # Attempt to connect to Redis
        r = redis.Redis(host='red-csne29aj1k6c73b1t0g0', port=6379, db=0)
        r.ping()  # This will raise an exception if the connection fails
        logger.info("Successfully connected to Redis.")
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")

# Example usage
if __name__ == "__main__":
    # Check Redis connection
    # check_redis_connection()

    # You can get stock_id from command line arguments or any other source
    stock_id = "2330"  # Example stock ID
    fetch_stock_news(stock_id)
    # run_spiders(stock_id)