from pydantic import BaseModel
from typing import Optional

class TelegramWebhook(BaseModel):
    update_id: int
    message: Optional[dict] = None
    callback_query: Optional[dict] = None
 