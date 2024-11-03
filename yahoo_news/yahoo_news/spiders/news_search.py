import scrapy
from pyquery import PyQuery
import redis
import json
from datetime import datetime, timedelta
from scrapy_redis.spiders import RedisSpider
from yahoo_news.items import ContentItem
from yahoo_news import settings


class NewsSearchSpider(scrapy.Spider):
    name = "news_search"
    start_urls = "https://finance.ettoday.net/search.php7"

    def __init__(self, stock_id=None, *args, **kwargs):
        super(NewsSearchSpider, self).__init__(*args, **kwargs)
        self.stock_id = stock_id or '2330' 
        self.redis_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT,
            db=0,
            )
    
    def start_requests(self):
        for page in range(1,3):
            url = f"{self.start_urls}?keyword={self.stock_id}&page={page}"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={'stock_id': self.stock_id, 'page': page}  # Pass metadata for reference in parse
            )

    def parse(self, response):
        reclient = redis.StrictRedis(connection_pool=self.redis_pool)
        dom = PyQuery(response.text)
        dom_list = dom(".part_pictxt_3 a")
        for item in dom_list.items():
            link = item.attr("href")
            if link:
                # Store both link and stock_id in Redis
                reclient.lpush("links", json.dumps({
                    "link": link, 
                    "stock_id": self.stock_id
                }))
                reclient.expire("links", settings.SECOND_IN_ONE_MONTH)

class ContentSpider(RedisSpider):
    name = "content"
    redis_key = "links"

    def make_request_from_data(self, data):
        # Parse the JSON data from Redis
        try:
            link_data = json.loads(data.decode('utf-8'))
            link = link_data["link"]
            stock_id = link_data["stock_id"]
            return scrapy.Request(url=link, meta={"stock_id": stock_id})
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON data: {e}")
        except KeyError as e:
            self.logger.error(f"Missing key in Redis data: {e}")
        return None

    def parse(self, response):
        stock_id = response.meta.get("stock_id")
        dom = PyQuery(response.text)
        title = dom("header h1.title").text()
        content = dom("div.story").text()
        date = dom("meta[name='pubdate']").attr("content")
        date = datetime.fromisoformat(date)
        item = ContentItem()
        item["stock_id"] = stock_id
        item["title"] = title
        item["content"] = content
        item["date"] = date
        item["url"] = response.url
        yield item