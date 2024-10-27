from dotenv import load_dotenv
import os

load_dotenv()

# Environment variables for better security in deployment
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN2", "your_telegram_token") 
WEBHOOK_SECRET_KEY = os.getenv("WEBHOOK_SECRET_KEY", "your_webhook_secret_key")
WEBHOOK_URL = os.getenv("WEBHOOK_URL1", "your_webhook_url")  