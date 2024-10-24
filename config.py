from dotenv import load_dotenv
import os

load_dotenv()

# Environment variables for better security in deployment
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_telegram_token")
 