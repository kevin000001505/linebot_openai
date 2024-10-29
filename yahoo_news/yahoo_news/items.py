# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Field, Item


class ContentItem(Item):
    title = Field()
    content = Field()
    date = Field()
    url = Field()
    stock_id = Field()

