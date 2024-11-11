# worker/celery_worker.py

import os
import sys
import logging
from celery_config import make_celery

# Configure logging
logging.basicConfig(level=logging.INFO)

# Ensure 'worker' directory is in PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
    logging.info(f"Appended {current_dir} to sys.path")
else:
    logging.info(f"{current_dir} already in sys.path")

try:
    from scrapy_runner import ScrapyRunner
    logging.info("Successfully imported ScrapyRunner")
except ModuleNotFoundError as e:
    logging.error(f"Failed to import ScrapyRunner: {e}")
    raise

# Initialize Celery
celery = make_celery(
    broker_url=os.environ.get('REDIS_URL'),
    backend_url=os.environ.get('REDIS_URL')
)

@celery.task(name='celery_worker.extract_stock_info', bind=True, max_retries=3, default_retry_delay=60)
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