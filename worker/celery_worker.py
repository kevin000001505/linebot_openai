# worker/celery_worker.py

import os
import sys
import logging
from celery import Celery

# Configure logging
logging.basicConfig(level=logging.INFO)

# Determine the absolute path of the current file (celery_worker.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Determine the project root directory (one level up)
project_root = os.path.dirname(current_dir)

# Append the project root to sys.path if it's not already included
if project_root not in sys.path:
    sys.path.append(project_root)
    logging.info(f"Appended project root '{project_root}' to sys.path")
else:
    logging.info(f"Project root '{project_root}' already in sys.path")

# Import make_celery after appending project_root to sys.path
try:
    from celery_config import make_celery
    logging.info("Successfully imported 'make_celery' from 'celery_config'")
except ModuleNotFoundError as e:
    logging.error(f"Failed to import 'celery_config': {e}")
    raise

# Import ScrapyRunner after ensuring project_root is in sys.path
try:
    from worker.scrapy_runner import ScrapyRunner
    logging.info("Successfully imported 'ScrapyRunner' from 'scrapy_runner'")
except ModuleNotFoundError as e:
    logging.error(f"Failed to import 'ScrapyRunner': {e}")
    raise

# Initialize Celery
celery = make_celery(
    broker_url=os.environ.get('REDIS_URL'),
    backend_url=os.environ.get('REDIS_URL')
)

@celery.task(name='worker.celery_worker.extract_stock_info', bind=True, max_retries=3, default_retry_delay=60)
def extract_stock_info(self, stock_id='2330'):
    """
    Celery task to execute Scrapy spiders for a given stock_id.
    Retries up to 3 times in case of failure, waiting 60 seconds between retries.
    """
    try:
        logging.info(f"Celery task started for stock_id: {stock_id}")
        scraper = ScrapyRunner()
        scraper.crawl_spiders(stock_id)
        logging.info(f"Celery task completed for stock_id: {stock_id}")
    except Exception as e:
        logging.error(f"Task failed for stock_id {stock_id}: {e}")
        self.retry(exc=e)