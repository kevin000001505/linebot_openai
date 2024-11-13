from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from twisted.internet import reactor, defer
from scrapy_proj.yahoo_news.spiders.news_search import NewsSearchSpider, AnueSearchSpider, ContentSpider

settings = get_project_settings()
process = CrawlerProcess(settings)

@defer.inlineCallbacks
def run_spiders(stock_id):
    yield defer.DeferredList([
    process.crawl(NewsSearchSpider),
    process.crawl(AnueSearchSpider)
])
    yield process.crawl(ContentSpider)
    reactor.stop()

# Example usage in the same file
if __name__ == "__main__":
    run_spiders(stock_id="2330")
    process.start()
