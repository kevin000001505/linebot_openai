import os


class Config:
    # LINE Bot
    CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
    CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

    # AWS S3
    AWS_ACCESS_KEY_ID = os.getenv("aws_access_key_id")
    AWS_SECRET_ACCESS_KEY = os.getenv("aws_secret_access_key")
    S3_BUCKET = "linebot-image-kevin"

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PREPLEXITY_API_KEY = os.getenv("PREPLEXITY_API_KEY")

    # Database
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    # Other configurations
    PORT = int(os.getenv("PORT", 5000))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Google Map API
    GOOGLE_MAP_API = os.getenv("GOOGLE_MAP_API")
