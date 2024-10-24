from fastapi import FastAPI
from models import TelegramWebhook
from handlers import handle_message, handle_callback_query

app = FastAPI()

@app.post("/forward")
async def forward_message(data: TelegramWebhook):
    if data.callback_query:
        await handle_callback_query(data.callback_query)
        return {"status": "ok", "message": "Callback query handled"}

    if data.message:
        message = data.message
        await handle_message(message)
        return {"status": "ok", "message": "Message handled"}

    return {"status": "ok", "message": "No relevant message to process"}
