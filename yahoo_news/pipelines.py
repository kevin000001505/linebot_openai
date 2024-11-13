# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from . import settings
import psycopg2

class PostgresPipeline:
    def __init__(self):
        self.pg_host = settings.DB_HOST
        self.pg_port = 5432
        self.pg_db = settings.DB_NAME
        self.pg_user = settings.DB_USER
        self.pg_password = settings.DB_PASSWORD

    def process_item(self, item, spider):
        # Only process items from ContentSpider
        if spider.name != 'content':
            return item
            
        try:
            self.cur.execute("""
                INSERT INTO articles (stock_id, title, date, url, content)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (
                item['stock_id'],
                item['title'],
                item['date'],
                item['url'],
                item['content'],
            ))
            self.conn.commit()
            spider.logger.info(f"Inserted: {item['url']}")
        except psycopg2.Error as e:
            self.conn.rollback()
            spider.logger.error(f"Failed to insert: {item['url']}")
        return item

    def open_spider(self, spider):
        # Only open connection for ContentSpider
        if spider.name != 'content':
            return
            
        self.conn = psycopg2.connect(
            host=self.pg_host,
            port=self.pg_port,
            dbname=self.pg_db,
            user=self.pg_user,
            password=self.pg_password
        )
        self.cur = self.conn.cursor()
        
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                stock_id INTEGER NOT NULL,
                title TEXT,
                date TIMESTAMP,
                url TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content TEXT
            )
        """)
        self.conn.commit()

    def close_spider(self, spider):
        # Only close connection for ContentSpider
        if spider.name != 'content':
            return
        self.cur.close()
        self.conn.close()