from db import (
    load_groups, set_user_state, get_user_state, delete_user_state,
    find_admin_by_id, find_admin_by_username, add_admin, is_admin_exists,
    get_admins, add_to_readymessageids, delete_user_messages, update_admin_info
)

from bot_utils import (
    bot, send_admin_welcome_message, send_group_list, send_broadcast_prompt,
    send_confirmation_prompt, send_admin_list_prompt, send_welcome_message
)

from telegram.error import TelegramError

# List of available bot admin_commands
admin_commands = ["/start", "/groups", "/broadcast", "/admins", "/addadmin", "/removeadmin", "/feedbacks"]
public_commands = ["/start", "/Join our medias", "/Feedback", "/About us"]


async def handle_public_commands(text, chat_id, message_id):
    if text == "/start":
        await send_welcome_message(chat_id)
    
    elif text == "/join our medias":
        await bot.send_message(
            chat_id=chat_id, 
            text="Join our media channels to stay updated with the latest news and community events!"
        )
        text = "Here are the lists of our media channels:\n\n1\\. [CSEC ASTU Telegram](https://t.me/CSEC_ASTU)\n2\\. [LinkedIn](https://www.linkedin.com/company/csec-astu/) \n3\\ [Tutorial Group](https://t.me/csec_tutorials/) \n4\\. [Youtube](https://www.youtube.com/@csec_cbd)"
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="MarkdownV2")

    
    elif text == "/feedback":
        await bot.send_message(
            chat_id=chat_id, 
            text="We’d love to hear from you! Please share your feedback below."
        )
        set_user_state(chat_id, "feedback")
        
    elif text == "/about us":
       await bot.send_message(
            chat_id=chat_id,
            text="""
        🌟 Welcome to CSEC ASTU 🌟\nCSEC ASTU is a student led community at Adama Science and Technology University that promotes programming and software development. 💻✨ \nWe provide a collaborative space for skill-sharing, workshops, and events aimed at enhancing your coding skills. 🚀🤝 \nJoin us to connect with peers, learn, and grow in the tech field For updates, check our social media 📱🌐
        """
        )

    
    else:
        # Handle user response if in feedback state
        state = get_user_state(chat_id)
        if state and state.get("state") == "feedback":
            await bot.forward_message(chat_id=-4512339292, from_chat_id=chat_id, message_id=message_id)
            
            await bot.send_message(
                chat_id=chat_id, 
                text="Thank you for your valuable feedback! We appreciate your time."
            )
            delete_user_state(chat_id)

    
    
async def handle_admin_commans(text, chat_id, user_info):
    """Handles various bot admin_commands based on user input text."""
    
    user_id = user_info["id"]
    
    if text == "/start":
        await send_admin_welcome_message(chat_id)
        update_admin_info(user_info)

    elif text == "/groups":
        groups = load_groups()
        await send_group_list(chat_id, groups)

    elif text == "/broadcast":
        set_user_state(user_id, "broadcast")
        delete_user_messages(user_id)
        await send_broadcast_prompt(chat_id)

    elif text == "/admins":
        admins = get_admins()
        await send_admin_list_prompt(chat_id, admins)

    elif text == "/addadmin":
        set_user_state(user_id, "add_admin")
        await bot.send_message(
            chat_id=chat_id,
            text="Please forward the message from the user you want to add as an admin, or simply send their username."
        )

    elif text == "/removeadmin":
        admins = get_admins()
        if not admins:
            await bot.send_message(chat_id=chat_id, text="There are no admins to remove.")
        else:
            await bot.send_message(chat_id=chat_id, text="Please select the admin you want to remove.")
            
    # elif text == '/feedbacks':
    #     feedbacks = get_feedbacks()
    #     if not feedbacks:
    #         await bot.send_message(chat_id=chat_id, text="There are no feedbacks to display.")
    #     else:
    #         await bot.send_message(chat_id=chat_id, text="Here are the feedbacks:\n\n" + "\n".join(feedback['feedback_text'] for feedback in feedbacks))
    
    return {"status": "ok"} 
 

async def handle_admin_addition(message, user_id, chat_id):
    """Handles the admin addition process based on user input."""
    if "forward_origin" in message:
        sender_user = message["forward_origin"].get("sender_user")
        if not sender_user:
            await bot.send_message(chat_id=chat_id, text="The forwarded user has a private profile. Try using their username.")
            return {"status": "ok"}

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
    
    return {"status": "ok"}


async def handle_broadcast(message, chat_id, user_id):
    """Handles broadcasting messages to groups."""
    from_chat_id = chat_id
    message_id = message["message_id"]

    if 'forward_origin' in message and message['forward_origin'].get('chat'):
        from_chat_id = message["forward_origin"]["chat"].get("id")
        message_id = message["forward_origin"]["message_id"]

    add_to_readymessageids(user_id, message_id)
    await send_confirmation_prompt(message['from']['id'], from_chat_id, message_id)
    return {"status": "ok"}


async def habdle_admin_message(message:dict):
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "").lower()
    state = get_user_state(user_id)
    
    if text in admin_commands:
        return await handle_admin_commans(text, chat_id, message['from'])

    # Handle states for admin addition or broadcasting
    if state and state.get("state") == "add_admin":
        return await handle_admin_addition(message, user_id, chat_id)

    if state and state.get("state") == "broadcast":
        return await handle_broadcast(message, chat_id, user_id)

    # Unrecognized input
    await bot.send_message(chat_id=chat_id, text=f"I don't understand what you are saying, {message['from']['first_name']}")
    return {"status": "ok"}



async def handle_message(message: dict):
    """Main handler for all user messages."""
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "").lower()
    state = get_user_state(user_id)

    # Check if the user is an admin
    is_admin = user_id == 5542174411 or find_admin_by_id(user_id) or find_admin_by_username(message['from'].get('username'))
    if not is_admin:
        await handle_public_commands(text, chat_id, message['message_id'])
        return {"status": "ok"}

    await habdle_admin_message(message)
    