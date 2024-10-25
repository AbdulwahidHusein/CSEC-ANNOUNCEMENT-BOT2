from telegram.error import TelegramError
from bot_utils import bot

from db import (
    load_groups, get_message_ids_by_user_id, delete_user_state, delete_user_messages,
    find_admin_by_id, find_admin_by_username
)

async def handle_callback_query(callback_query: dict):
    """Handles callback queries for message forwarding confirmation or cancellation."""
    from_id = callback_query["from"]["id"]
    data = callback_query["data"]

    # Confirm if the user is an admin
    is_admin = from_id == 5542174411 or find_admin_by_id(from_id) or find_admin_by_username(callback_query['from'].get('username'))
    if not is_admin:
        return {"status": "ok"}

    # Handle forward or cancel actions
    if data == "cancel-forward":
        delete_user_messages(from_id)
        await bot.send_message(chat_id=from_id, text="Message forwarding cancelled")
        await bot.delete_message(chat_id=from_id, message_id=callback_query["message"]["message_id"])


    elif data.startswith("forward:"):
        _, from_chat_id, message_id = data.split(":")
        from_chat_id, message_id = int(from_chat_id), int(message_id)

        groups = load_groups()
        forwarded_groups = []
        message_ids = get_message_ids_by_user_id(from_id)

        if message_ids:
            await bot.send_message(chat_id=from_id, text="Forwarding message to all groups...")
            for group in groups:
                try:
                    await bot.forward_messages(chat_id=group["id"], from_chat_id=from_chat_id, message_ids=message_ids)
                    forwarded_groups.append(group)
                except TelegramError as e:
                    await bot.send_message(chat_id=from_id, text=f"Error forwarding message to group {group['title']}: {e}")

            if forwarded_groups:
                response = "Message forwarded to the following groups:\n" + \
                           "".join(f"{group['title']} (@{group.get('username', 'NA')})\n" for group in forwarded_groups)
                await bot.send_message(chat_id=from_id, text=response)

            delete_user_state(from_id)
            delete_user_messages(from_id)
            
            await bot.delete_message(chat_id=from_id, message_id=callback_query["message"]["message_id"])

        else:
            await bot.send_message(chat_id=from_id, text="No message to forward")

    return {"status": "ok"}
