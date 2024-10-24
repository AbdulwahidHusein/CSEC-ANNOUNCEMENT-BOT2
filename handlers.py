from db import (
    load_groups, save_group, set_user_state, get_user_state, delete_user_state,
    find_admin_by_id, find_admin_by_username, add_admin, is_admin_exists, get_admins
)
from bot_utils import bot, send_welcome_message, send_group_list, send_broadcast_prompt, send_confirmation_prompt, send_admin_list_prompt
from telegram.error import TelegramError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def handle_message(message: dict): 
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    state = get_user_state(user_id)
    
    text = message.get("text", "").lower()

    # Start command
    if text == "/start":
        await send_welcome_message(chat_id)
        return {"status": "ok", "message": "Welcome message sent"}

    # Groups command
    if text == "/groups":
        groups = load_groups()
        await send_group_list(chat_id, groups)
        return {"status": "ok", "message": "Groups list sent"}

    # Broadcast command
    if text == "/broadcast":
        set_user_state(user_id, "broadcast")
        await send_broadcast_prompt(chat_id)
        return {"status": "ok", "message": "Broadcast state set"}

    # Admins command - list all admins
    if text == "/admins":
        admins = get_admins()
        await send_admin_list_prompt(chat_id, admins)
        return {"status": "ok", "message": "Admins list sent"}

    # Add Admin command
    if text == "/addadmin":
        set_user_state(user_id, "add_admin")
        await bot.send_message(chat_id=chat_id, text="Please forward the message from the user you want to add as an admin.")
        return {"status": "ok", "message": "Add admin state set"}
    
    if text == "/removeadmin":
        admins = get_admins()
        if not admins:
            await bot.send_message(chat_id=chat_id, text="There are no admins to remove.")
            return {"status": "ok", "message": "No admins to remove"}
        await bot.send_message(chat_id=chat_id, text="Please select the admin you want to remove.")
        
    # Handle admin addition process
    if state and state.get("state") == "add_admin":
        if message.get("forward_origin"):
            sender_user = message["forward_origin"].get("sender_user")
            
            if not sender_user:
                await bot.send_message(chat_id=chat_id, text="The forwarded user has a private profile, and their information cannot be accessed. Please send their username directly.")
                return {"status": "ok", "message": "Private profile"}

            admin_data = {
                "id": sender_user["id"],
                "username": sender_user.get("username"),
                "first_name": sender_user.get("first_name"),
                "last_name": sender_user.get("last_name")
            }
            

            # Check if there's already an admin with the same id and username
            existing_admin = is_admin_exists(admin_data)

            if existing_admin:
                await bot.send_message(chat_id=chat_id, text="Admin with this ID or username already exists.")
            else:
                add_admin(admin_data)
                await bot.send_message(chat_id=chat_id, text="Admin added successfully!")
                delete_user_state(user_id)

        elif "text" in message and message['text']:
            admin_data = {
                "id": None,
                "username": message['text'],
                "first_name": None,
                "last_name": None
            }

            existing_admin = find_admin_by_username(admin_data["username"])

            if existing_admin:
                await bot.send_message(chat_id=chat_id, text=f"@{admin_data['username']} is already an admin.")
            else:
                add_admin(admin_data)
                await bot.send_message(chat_id=chat_id, text="Admin added successfully!")
            
            delete_user_state(user_id)

        else:
            await bot.send_message(chat_id=chat_id, text="Something went wrong. Please try again.")
            
        return {"status": "ok", "message": "Admin added"}

    # Handle broadcast state
    if state and state.get("state") == "broadcast":
        await send_confirmation_prompt(chat_id, message["message_id"])
        return {"status": "ok", "message": "Confirmation message sent"}

    return {"status": "ok", "message": "No relevant state or command handled"}


async def handle_callback_query(callback_query: dict):
    """Handle callback queries for confirmation."""
    from_id = callback_query["from"]["id"]
    data = callback_query["data"]

    if data == "cancel-forward":
        await bot.send_message(chat_id=from_id, text="Message forwarding cancelled")
        return {"status": "ok", "message": "Message forwarding cancelled"}

    if data.startswith("forward:"):
        _, from_chat_id, message_id = data.split(":")
        from_chat_id = int(from_chat_id)
        message_id = int(message_id)

        groups = load_groups()
        for group in groups:
            try:
                await bot.forward_message(chat_id=group["id"], from_chat_id=from_chat_id, message_id=message_id)
            except TelegramError as e:
                print(f"Error forwarding message to group {group['id']}: {e}")

        await bot.send_message(chat_id=from_id, text="Message forwarded to all groups")
        delete_user_state(from_id)
        return {"status": "ok", "message": "Message forwarded to all groups"}
