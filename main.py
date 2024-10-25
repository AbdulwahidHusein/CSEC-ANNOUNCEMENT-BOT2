from fastapi import FastAPI, Request, Path
from fastapi.responses import JSONResponse
from models import TelegramWebhook
from handlers import handle_message, handle_callback_query
from db import add_group
import config
from telegram import Bot
from logging import getLogger, StreamHandler, Formatter
import logging

# Initialize logger
logger = getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler for logging
console_handler = StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

async def lifespan(app: FastAPI):
    """App lifespan event to set the Telegram bot webhook on startup."""
    bot = Bot(token=config.TOKEN)
    try:
        await bot.set_webhook(url=config.WEBHOOK_URL, secret_token=config.WEBHOOK_SECRET_KEY)
        logger.info(f"Webhook set successfully: {config.WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
    yield

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def verify_telegram_secret_token(request: Request, call_next):
    """Middleware to verify Telegram's secret token in incoming requests."""
    
    
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    
    if secret_token != config.WEBHOOK_SECRET_KEY:
        logger.error("Unauthorized request: Invalid secret token")
        return JSONResponse(status_code=403, content={"detail": "Unauthorized request"})

    response = await call_next(request)
    return response


@app.post("/broadcasting-bot") 
async def forward_message(data: TelegramWebhook):
    """Endpoint to handle incoming Telegram webhook data."""
    try:
        if data.callback_query:
            await handle_callback_query(data.callback_query)
            logger.info("Callback query handled successfully")
            return {"status": "ok", "message": "Callback query handled"}
         
        if data.message and data.message.get("new_chat_participant"):
            group_data = data.message["chat"] 
            add_group(group_data)
         
        if data.message:
            message = data.message
            await handle_message(message)
            logger.info("Message handled successfully")
            return {"status": "ok", "message": "Message handled"}

        logger.warning("No relevant message or callback query to process")
        return {"status": "ok", "message": "No relevant message to process"}

    except Exception as e:
        logger.error(f"Error processing webhook data: {e}")
        # raise HTTPException(status_code=500, detail="Internal server error")
        return {"status": "ok", "message": "Error processing webhook data"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to capture and log errors."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An error occurred while processing your request."}
    )
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
