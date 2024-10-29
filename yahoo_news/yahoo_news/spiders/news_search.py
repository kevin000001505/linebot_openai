import scrapy
from pyquery import PyQuery
import redis
from datetime import datetime, timedelta
from scrapy_redis.spiders import RedisSpider
from yahoo_news.items import ContentItem
from yahoo_news import settings


class NewsSearchSpider(scrapy.Spider):
    name = "news_search"
    allowed_domains = ["tw.stock.yahoo.com"]
    start_urls = ["https://tw.stock.yahoo.com/quote/2314.TW"]

    def __init__(self, stock_id, *args, **kwargs):
        super(NewsSearchSpider, self).__init__(*args, **kwargs)
        self.stock_id = stock_id
        item = ContentItem()
        item["stock_id"] = stock_id
        if stock_id:
            self.start_urls = [f"https://tw.stock.yahoo.com/quote/{stock_id}.TW"]
        else:
            self.start_urls = ["https://tw.stock.yahoo.com/quote/2330.TW"]
        self.redis_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT,
            )
    def parse(self, response):
        dom = PyQuery(response.text)
        dom_list = dom("#module-wafer-stream li h3 a")
        for item in dom_list.items():
            reclient = redis.StrictRedis(connection_pool=self.redis_pool)
            link = item.attr("href")
            if link:
                reclient.lpush("links", link)
                reclient.expire("links", settings.SECOND_IN_ONE_MONTH)

class ContentSpider(RedisSpider):
    name = "content"

    redis_key = "links"
    def parse(self, response):
        dom = PyQuery(response.text)
        title = dom("#module-article h1").text()
        content = dom(".caas-body").text()
        date = dom("#module-article time").attr("datetime")
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
        item = ContentItem()
        item["title"] = title
        item["content"] = content
        item["date"] = date
        item["url"] = response.url
        yield {
            "title": title,
            "content": content,
            "date": date.strftime("%Y-%m-%d %H:%M:%S"),
            "url": response.url,
        }
        return item