# celery_worker.py

import os
import sys
from celery_config import make_celery
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer
import logging
from threading import Thread

# Initialize Celery
celery = make_celery(
    broker_url=os.environ.get('REDIS_URL'),
    backend_url=os.environ.get('REDIS_URL')
)

class ScrapyRunner:
    def __init__(self):
        # Determine the project root directory
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Set the Scrapy settings module environment variable
        os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'yahoo_news.yahoo_news.settings')
        
        # Get Scrapy project settings
        self.settings = get_project_settings()
        
        # Initialize CrawlerRunner with project settings
        self.runner = CrawlerRunner(self.settings)
        
        # Start the Twisted reactor in a separate thread
        self.start_reactor()
        
    def start_reactor(self):
        if not reactor.running:
            def run_reactor():
                reactor.run(installSignalHandlers=0)  # Don't install signal handlers
            reactor_thread = Thread(target=run_reactor, daemon=True)
            reactor_thread.start()

    @defer.inlineCallbacks
    def crawl_spiders(self, stock_id):
        """
        Asynchronously run the 'news_search' and 'content' spiders with the given stock_id.
        """
        try:
            # Start crawling with 'news_search' spider
            yield self.runner.crawl('news_search', stock_id=str(stock_id))
            
            # Start crawling with 'content' spider
            yield self.runner.crawl('content', stock_id=str(stock_id))
            
            logging.info(f"Crawling completed for stock_id: {stock_id}")
        except Exception as e:
            logging.error(f"Error during crawling for stock_id {stock_id}: {e}")
            raise e

# Initialize ScrapyRunner instance
scraper = ScrapyRunner()

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
@defer.inlineCallbacks
def extract_stock_info(self, stock_id='2330'):
    """
    Celery task to execute Scrapy spiders for a given stock_id.
    Retries up to 3 times in case of failure, waiting 60 seconds between retries.
    """
    try:
        # Trigger the crawling process
        yield scraper.crawl_spiders(stock_id)
    except Exception as e:
        logging.error(f"Task failed for stock_id {stock_id}: {e}")
        # Retry the task in case of failure
        raise self.retry(exc=e)