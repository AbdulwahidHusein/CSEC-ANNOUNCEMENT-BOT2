from db import (
    load_groups, save_group, set_user_state, get_user_state, delete_user_state,
    find_admin_by_id, find_admin_by_username, add_admin, is_admin_exists, get_admins
)
from bot_utils import (
    bot, send_welcome_message, send_group_list, send_broadcast_prompt,
    send_confirmation_prompt, send_admin_list_prompt
)
from telegram.error import TelegramError

commands = ["/start", "/groups", "/broadcast", "/admins", "/addadmin", "/removeadmin"]


async def handle_command(text, chat_id, user_id):
    """Handle different commands based on the user's input text."""
    if text == "/start":
        await send_welcome_message(chat_id)
        return {"status": "ok", "message": "Welcome message sent"}

    if text == "/groups":
        groups = load_groups()
        await send_group_list(chat_id, groups)
        
        return {"status": "ok", "message": "Groups list sent"}

    if text == "/broadcast":
        set_user_state(user_id, "broadcast")
        await send_broadcast_prompt(chat_id)
        return {"status": "ok", "message": "Broadcast state set"}

    if text == "/admins":
        admins = get_admins()
        await send_admin_list_prompt(chat_id, admins)
        return {"status": "ok", "message": "Admins list sent"}

    if text == "/addadmin":
        set_user_state(user_id, "add_admin")
        await bot.send_message(
            chat_id=chat_id, text="Please forward the message from the user you want to add as an admin. or simpley send me a username"
        )
        return {"status": "ok", "message": "Add admin state set"}

    if text == "/removeadmin":
        admins = get_admins()
        if not admins:
            await bot.send_message(chat_id=chat_id, text="There are no admins to remove.")
            return {"status": "ok", "message": "No admins to remove"}
        await bot.send_message(chat_id=chat_id, text="Please select the admin you want to remove.")
        return {"status": "ok", "message": "Remove admin process started"}

    return {"status": "ok", "message": "No relevant command found"}


async def handle_admin_addition(message, user_id, chat_id):
    """Handle the admin addition process."""
    if message.get("forward_origin"):
        sender_user = message["forward_origin"].get("sender_user")
        if not sender_user:
            await bot.send_message(chat_id=chat_id, text="The forwarded user has a private profile. try using their username")
            return {"status": "ok", "message": "Private profile"}

        admin_data = {
            "id": sender_user["id"],
            "username": sender_user.get("username"),
            "first_name": sender_user.get("first_name"),
            "last_name": sender_user.get("last_name")
        }

        if is_admin_exists(admin_data):
            await bot.send_message(chat_id=chat_id, text="Admin with this ID or username already exists.")
        else:
            add_admin(admin_data)
            await bot.send_message(chat_id=chat_id, text="Admin added successfully!")
        delete_user_state(user_id)
    elif "text" in message and message['text']:
        username = message['text']
        if find_admin_by_username(username):
            await bot.send_message(chat_id=chat_id, text=f"@{username} is already an admin.")
        else:
            add_admin({"id": None, "username": username})
            await bot.send_message(chat_id=chat_id, text="Admin added successfully!")
        delete_user_state(user_id)
    else:
        await bot.send_message(chat_id=chat_id, text="Something went wrong. Please try again.")
    return {"status": "ok", "message": "Admin added process handled"}


async def handle_broadcast(message, chat_id):
    """Handle broadcast messages."""
    
    from_chat_id = chat_id
    message_id = message["message_id"]
    if 'forward_origin' in message and message['forward_origin'].get('chat'):
        from_chat_id = message["forward_origin"]["chat"].get("id")
        message_id = message["forward_origin"]["message_id"]
    
    await send_confirmation_prompt(message['from']['id'], from_chat_id, message_id)
    return {"status": "ok", "message": "Confirmation message sent"}


async def handle_message(message: dict):
    """Main handler for user messages."""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "").lower()
    state = get_user_state(user_id)
    
    is_admin  = user_id == 5542174411
    if not is_admin:
        is_admin = find_admin_by_id(user_id)
    if not is_admin:
        if 'username' in message['from']:
            is_admin = find_admin_by_username(message['from']['username'])
    if not is_admin:
        return {"status": "ok", "message": "User is not an admin"}

    if text in commands:
        return await handle_command(text, chat_id, user_id)

    if state and state.get("state") == "add_admin":
        return await handle_admin_addition(message, user_id, chat_id)

    if state and state.get("state") == "broadcast":
        return await handle_broadcast(message, chat_id)

    await bot.send_message(chat_id=chat_id, text=f"I don't understand what you are saying, {message['from']['first_name']}")
    return {"status": "ok", "message": "Unrecognized state or command"}


async def handle_callback_query(callback_query: dict):
    """Handle callback queries for confirmation."""
   
    from_id = callback_query["from"]["id"]
    
    is_admin  = from_id == 5542174411
    if not is_admin:
        is_admin = find_admin_by_id(from_id)
    if not is_admin:
        if 'username' in callback_query['from']:
            is_admin = find_admin_by_username(callback_query['from']['username'])
    if not is_admin:
        return {"status": "ok", "message": "User is not an admin"}

    data = callback_query["data"]

    if data == "cancel-forward":
        await bot.send_message(chat_id=from_id, text="Message forwarding cancelled")
        return {"status": "ok", "message": "Message forwarding cancelled"}

    if data.startswith("forward:"):
        _, from_chat_id, message_id = data.split(":")
        from_chat_id, message_id = int(from_chat_id), int(message_id)

        groups = load_groups()
        forwarded_groups = []
        await bot.send_message(chat_id=from_id, text="Forwarding message to all groups...")

        for group in groups:
            try:
                await bot.forward_message(chat_id=group["id"], from_chat_id=from_chat_id, message_id=message_id)
                forwarded_groups.append(group)
            except TelegramError as e:
                
                await bot.send_message(chat_id=from_id, text=f"Error forwarding message to group {group['id']}: {e}")
                if forwarded_groups:
                    response = "Still, Message forwarded to the following groups:\n" + " ".join(
                        [f"{group['title']} (@{group.get('username', 'NA')})\n" for group in forwarded_groups if group]
                    )
                    await bot.send_message(chat_id=from_id, text=response)
        
        if forwarded_groups:
            response = "Message forwarded to the following groups:\n" + " ".join(
                [f"{group['title']} (@{group.get('username', 'NA')})\n" for group in forwarded_groups if group]
            )
            await bot.send_message(chat_id=from_id, text=response)
        
        delete_user_state(from_id)
        return {"status": "ok", "message": "Message forwarded to all groups"}    
