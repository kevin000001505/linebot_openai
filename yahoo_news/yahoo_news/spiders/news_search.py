import scrapy
from pyquery import PyQuery
import redis
from datetime import datetime, timedelta
from scrapy_redis.spiders import RedisSpider
from .. import settings

redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT,
)

class NewsSearchSpider(scrapy.Spider):
    name = "news_search"
    allowed_domains = ["tw.stock.yahoo.com"]
    start_urls = ["https://tw.stock.yahoo.com/quote/2314.TW"]

    def parse(self, response):
        dom = PyQuery(response.text)
        dom_list = dom("#module-wafer-stream li h3 a")
        for item in dom_list.items():
            reclient = redis.StrictRedis(connection_pool=redis_pool)
            link = item.attr("href")
            if link:
                reclient.lpush("links", link)
                reclient.expire("links", settings.SECOND_IN_ONE_MONTH)


    def date_recognize(self, orginal_date):
        today = datetime.now()
        num = int(orginal_date.split(" ")[0])
        if "月" in orginal_date and num <= 2:
            date = today - timedelta(days=30*num)
            return date
        elif "天" in orginal_date:
            date = today - timedelta(days=num)
            return date
        else:
            return None

class ContentSpider(RedisSpider):
    name = "content"

    redis_key = "links"
    def parse(self, response):
        dom = PyQuery(response.text)
        title = dom("#module-article h1").text()
        content = dom(".caas-body").text()
        date = dom("#module-article time").attr("datetime")
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
        yield {
            "title": title,
            "content": content,
            "date": date.strftime("%Y-%m-%d %H:%M:%S"),
            "url": response.url,
        }