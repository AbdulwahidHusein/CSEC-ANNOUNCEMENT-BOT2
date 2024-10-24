from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from models import TelegramWebhook
from handlers import handle_message, handle_callback_query
import config
from telegram import Bot
from logging import getLogger

logger = getLogger(__name__)

async def lifespan(app):
    bot = Bot(token=config.TOKEN)
    try:
       await bot.set_webhook(url=config.WEBHOOK_URL, secret_token=config.WEBHOOK_SECRET_KEY)
    except Exception as e:
        print(f"Error setting webhook: {e}")
    
    yield

app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def verify_telegram_secret_token(request: Request, call_next):
    
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    
    if secret_token != config.WEBHOOK_SECRET_KEY:
        logger.error(f"Unauthorized request: Invalid secret token")
        return JSONResponse(status_code=403, content={"detail": "Unauthorized request"})
     
    response = await call_next(request)
    return response



@app.post("/broadcasting-bot")
async def forward_message(data: TelegramWebhook):
    
    if data.callback_query:
        await handle_callback_query(data.callback_query)
        return {"status": "ok", "message": "Callback query handled"}

    if data.message:
        message = data.message
        await handle_message(message)
        return {"status": "ok", "message": "Message handled"}

    return {"status": "ok", "message": "No relevant message to process"}
