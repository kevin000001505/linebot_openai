# worker/scrapy_runner.py

import os
import sys
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer
import logging
from threading import Thread

class ScrapyRunner:
    def __init__(self):
        # Determine the project root directory
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        logging.info(f"ScrapyRunner initialized in {project_root}")

        # Set the Scrapy settings module environment variable
        os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'yahoo_news.settings')
        logging.info("SCRAPY_SETTINGS_MODULE set to 'yahoo_news.settings'")

        # Get Scrapy project settings
        self.settings = get_project_settings()
        logging.info("Scrapy settings loaded")

        # Initialize CrawlerRunner with project settings
        self.runner = CrawlerRunner(self.settings)
        logging.info("CrawlerRunner initialized")

        # Start the Twisted reactor in a separate thread
        self.start_reactor()

    def start_reactor(self):
        if not reactor.running:
            def run_reactor():
                reactor.run(installSignalHandlers=0)  # Don't install signal handlers
            reactor_thread = Thread(target=run_reactor, daemon=True)
            reactor_thread.start()
            logging.info("Twisted reactor started in a separate thread")
        else:
            logging.info("Twisted reactor already running")

    @defer.inlineCallbacks
    def crawl_spiders(self, stock_id):
        """
        Asynchronously run the 'news_search' and 'content' spiders with the given stock_id.
        """
        try:
            logging.info(f"Starting crawling for stock_id: {stock_id}")
            # Start crawling with 'news_search' spider
            yield self.runner.crawl('news_search', stock_id=str(stock_id))
            logging.info(f"Started 'news_search' spider for stock_id: {stock_id}")

            # Start crawling with 'content' spider
            yield self.runner.crawl('content', stock_id=str(stock_id))
            logging.info(f"Started 'content' spider for stock_id: {stock_id}")

            logging.info(f"Crawling completed for stock_id: {stock_id}")
        except Exception as e:
            logging.error(f"Error during crawling for stock_id {stock_id}: {e}")
            raise e