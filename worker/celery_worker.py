# worker/celery_worker.py

import os
import sys
import logging
from run_spiders import run_spiders


# Import make_celery after appending project_root to sys.path
try:
    from celery_config import make_celery
    logging.info("Successfully imported 'make_celery' from 'celery_config'")
except ModuleNotFoundError as e:
    logging.error(f"Failed to import 'celery_config': {e}")
    raise


# Initialize Celery
celery = make_celery(
    broker_url=os.environ.get('REDIS_URL'),
    backend_url=os.environ.get('REDIS_URL')
)

@celery.task(name='worker.celery_worker.fetch_stock_news', bind=True, max_retries=3, default_retry_delay=60)
def fetch_stock_news(self, stock_id='2330'):
    """
    Celery task to execute Scrapy spiders for a given stock_id.
    Retries up to 3 times in case of failure, waiting 60 seconds between retries.
    """
    try:
        run_spiders(stock_id=stock_id)
        logging.info(f"Celery task completed for stock_id: {stock_id}")
    except Exception as e:
        logging.error(f"Task failed for stock_id {stock_id}: {e}")
        self.retry(exc=e)