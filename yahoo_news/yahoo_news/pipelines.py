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

    def open_spider(self, spider):
        # Connect to PostgreSQL when spider starts
        self.conn = psycopg2.connect(
            host=self.pg_host,
            port=self.pg_port,
            dbname=self.pg_db,
            user=self.pg_user,
            password=self.pg_password
        )
        self.cur = self.conn.cursor()
        
        # Create table if it doesn't exist
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                stock_id INTEGER NOT NULL,
                title TEXT,
                content TEXT,
                date TIMESTAMP,
                url TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def close_spider(self, spider):
        # Close PostgreSQL connection when spider finishes
        self.cur.close()
        self.conn.close()

    def process_item(self, item, spider):
        # Check if URL already exists
        self.cur.execute("""
            SELECT url FROM articles WHERE url = %s
        """, (item['url'],))
        
        exists = self.cur.fetchone()
        
        if not exists:
            # Insert item into PostgreSQL only if URL doesn't exist
            self.cur.execute("""
                INSERT INTO articles (stock_id, title, content, date, url)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                item['stock_id'],
                item['title'],
                item['content'],
                item['date'],
                item['url']
            ))
            self.conn.commit()
            spider.logger.info(f"Inserted new article: {item['url']}")
        else:
            spider.logger.info(f"Skipped duplicate article: {item['url']}")
            
        return item