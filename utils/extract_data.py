import psycopg2
import json
from datetime import datetime, timedelta
from config import Config


def pg_extract(stock_id):
    conn = psycopg2.connect(
        host=Config.DB_HOST,
        port=6379,
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
    )
    cur = conn.cursor()
    
    # Get data from last 30 days
    cur.execute(f"""
        SELECT id, title, content, url, date 
        FROM articles
        WHERE date >= NOW() - INTERVAL '30 days' AND stock_id = {stock_id}
        ORDER BY date DESC
    """)
    
    # Fetch all results
    rows = cur.fetchall()
    
    # Convert to list of dictionaries
    articles = []
    for row in rows:
        article = {
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'url': row[3],
            'date': row[4].isoformat() if row[4] else None
        }
        articles.append(article)
    
    cur.close()
    conn.close()
    
    return articles
