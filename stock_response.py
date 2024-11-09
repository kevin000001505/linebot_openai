import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import logging

class ScrapyRunner:
    def __init__(self):
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        # Set the module name for settings
        os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'yahoo_news.yahoo_news.settings')
        self.settings = get_project_settings()
        self.process = CrawlerProcess(self.settings)
        
    def Extract_Stock_info(self, stock_id=None):
        """
        Run both spiders in sequence
        """
        try:
            # Add both spiders to the process
            self.process.crawl('news_search', stock_id=stock_id)
            self.process.crawl('content')
            
            # Start the process
            self.process.start()
            
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            raise e

    def run_yahoo_crawler(self, stock_id):
        try:
            self.Extract_Stock_info(stock_id=str(stock_id))
        except Exception as e:
            logging.error(f"Error in crawler: {str(e)}")
            raise e