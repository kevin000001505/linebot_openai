from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from yahoo_news.spiders.news_search import NewsSearchSpider, AnueSearchSpider, ContentSpider
# 1. Install the AsyncioSelectorReactor before any other imports
configure_logging({"LOG_FORMAT": "%(levelname)s: %(message)s"})
runner = CrawlerRunner()

@defer.inlineCallbacks
def run_spider(stock_id):
    yield runner.crawl(NewsSearchSpider, stock_id=stock_id)
    yield runner.crawl(AnueSearchSpider, stock_id=stock_id)
    yield runner.crawl(ContentSpider)
    reactor.stop()
    # d = runner.join()
    # d.addBoth(lambda _: reactor.stop())
    # reactor.run()

def run_spiders(stock_id):
    run_spider(stock_id='2330')
    reactor.run()


# Example usage in the same file
if __name__ == "__main__":
    run_spiders(stock_id="2330")
    