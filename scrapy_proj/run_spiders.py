from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy_proj.yahoo_news.spiders.news_search import NewsSearchSpider, AnueSearchSpider, ContentSpider

class NewsSpiderRunner:
    def __init__(self):
        self.settings = get_project_settings()
        self.process = CrawlerProcess(self.settings)
    
    def run_spiders(self, stock_id='2330'):
        """
        Run all spiders sequentially with the given stock_id
        """
        self.process.crawl(NewsSearchSpider, stock_id=stock_id)
        self.process.crawl(AnueSearchSpider, stock_id=stock_id)
        self.process.crawl(ContentSpider)
        self.process.start()

# Example usage in the same file
if __name__ == "__main__":
    runner = NewsSpiderRunner()
    runner.run_spiders(stock_id="2330")