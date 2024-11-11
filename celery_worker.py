# worker/celery_worker.py

import os
from celery_config import make_celery
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Celery
celery = make_celery(
    broker_url=os.environ.get('REDIS_URL'),
    backend_url=os.environ.get('REDIS_URL')
)

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def extract_stock_info(self, stock_id='2330'):
    """
    Celery task to execute Scrapy spiders for a given stock_id.
    Retries up to 3 times in case of failure, waiting 60 seconds between retries.
    """
    try:
        logging.info(f"Celery task started for stock_id: {stock_id}")
        # Import ScrapyRunner within the task to prevent initialization during import
        from scrapy_runner import ScrapyRunner
        scraper = ScrapyRunner()
        scraper.crawl_spiders(stock_id)
    except Exception as e:
        logging.error(f"Task failed for stock_id {stock_id}: {e}")
        # Retry the task in case of failure
        self.retry(exc=e)