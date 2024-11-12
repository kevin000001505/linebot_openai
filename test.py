from worker.celery_worker import fetch_stock_news

# Example usage
if __name__ == "__main__":
    # You can get stock_id from command line arguments or any other source
    stock_id = "2330"  # Example stock ID
    fetch_stock_news(stock_id)