from twisted.internet import reactor, defer # type: ignore
from scrapy.crawler import CrawlerRunner # type: ignore
from scrapy.utils.log import configure_logging # type: ignore
from twisted.internet.asyncioreactor import AsyncioSelectorReactor # type: ignore
import asyncio
from yahoo_news.spiders.news_search import NewsSearchSpider, AnueSearchSpider, ContentSpider

configure_logging({"LOG_FORMAT": "%(levelname)s: %(message)s"})

def create_crawler_runner():
    return CrawlerRunner()

@defer.inlineCallbacks
def crawl(runner, stock_id):
    yield runner.crawl(NewsSearchSpider, stock_id=stock_id)
    yield runner.crawl(AnueSearchSpider, stock_id=stock_id)
    yield runner.crawl(ContentSpider)
    
async def run_spiders_async(stock_id):
    # Install AsyncioSelectorReactor if reactor not yet installed
    if not reactor.running:
        reactor._initInstalled = False
        AsyncioSelectorReactor().install()
    
    runner = create_crawler_runner()
    deferred = crawl(runner, stock_id)
    deferred.addBoth(lambda _: reactor.stop())
    
    # Run reactor in a separate thread
    reactor_thread = asyncio.get_event_loop()
    await asyncio.get_event_loop().run_in_executor(None, reactor.run, True)
    return True

def run_spiders(stock_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(run_spiders_async(stock_id))

# Example usage in the same file
if __name__ == "__main__":
    run_spiders(stock_id="2330")