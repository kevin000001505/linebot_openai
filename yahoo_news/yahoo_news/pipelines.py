# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from . import settings
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import psycopg2
import asyncio
from concurrent.futures import ThreadPoolExecutor

rephrase_llm = ChatOpenAI(
    openai_api_key=settings.OPENAI_API_KEY,
    model_name="gpt-4o-mini",
    temperature=0.6,
    max_tokens=2048,
)

class PostgresPipeline:
    def __init__(self):
        self.pg_host = settings.DB_HOST
        self.pg_port = 5432
        self.pg_db = settings.DB_NAME
        self.pg_user = settings.DB_USER
        self.pg_password = settings.DB_PASSWORD
        self.items_buffer = []
        self.buffer_size = 5  # Process 5 items at a time
        self.executor = ThreadPoolExecutor(max_workers=5)  # For DB operations

    async def clean_data_async(self, content: str) -> str:
        content = content.replace('\n', '').replace('\u200c', '').strip()
        content = ' '.join(content.split())
        rephrase_prompt = PromptTemplate(template="""
        系统提示：您是一個專業的文本清理助手，請根據文章title，把廣告類的內容去除，並不用把 title 也輸出出來。

        文章內容：{content}

        After Data Cleaning：
        """,
        input_variables=["content"])

        rephrase_chain = LLMChain(
            llm=rephrase_llm,
            prompt=rephrase_prompt,
            verbose=False
        )

        cleaned_content = await rephrase_chain.arun(content=content)
        return cleaned_content

    def db_insert(self, item):
        try:
            self.cur.execute("""
                INSERT INTO articles (stock_id, title, content, date, url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (
                item['stock_id'],
                item['title'],
                item['content'],
                item['date'],
                item['url']
            ))
            self.conn.commit()
            return True
        except psycopg2.Error as e:
            self.conn.rollback()
            return False

    async def process_batch(self, items, spider):
        # Clean content in parallel
        cleaning_tasks = []
        for item in items:
            if spider.name == "content":
                title = item['title'].strip()
                item['title'] = title
                content = item['content']
                input_data = f"title: '{title}'. content: {content}"
                # Create task for cleaning
                task = asyncio.create_task(self.clean_data_async(input_data))
                cleaning_tasks.append(task)
            else:
                cleaning_tasks.append(None)

        # Wait for all cleaning tasks to complete
        if cleaning_tasks:
            cleaned_contents = await asyncio.gather(*[task for task in cleaning_tasks if task is not None])
            
            # Update items with cleaned content
            cleaned_idx = 0
            for item in items:
                if spider.name == "content":
                    item['content'] = cleaned_contents[cleaned_idx]
                    cleaned_idx += 1

        # Insert into database using thread pool
        loop = asyncio.get_event_loop()
        insert_tasks = []
        for item in items:
            insert_tasks.append(
                loop.run_in_executor(self.executor, self.db_insert, item)
            )
        
        results = await asyncio.gather(*insert_tasks)
        
        for item, success in zip(items, results):
            if success:
                spider.logger.info(f"Processed and inserted: {item['url']}")
            else:
                spider.logger.error(f"Failed to insert: {item['url']}")

    def process_item(self, item, spider):
        self.items_buffer.append(item)
        
        if len(self.items_buffer) >= self.buffer_size:
            asyncio.create_task(self.process_batch(self.items_buffer.copy(), spider))
            self.items_buffer = []
        
        return item

    def open_spider(self, spider):
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
                content TEXT,
                date TIMESTAMP,
                url TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def close_spider(self, spider):
        # Process remaining items
        if self.items_buffer:
            asyncio.run(self.process_batch(self.items_buffer, spider))
        
        self.executor.shutdown()
        self.cur.close()
        self.conn.close()