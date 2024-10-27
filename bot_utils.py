from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.error import TelegramError
from config import TOKEN
from db import get_admins, add_group, remove_group

bot = Bot(token=TOKEN)


def send_admin_welcome_message(chat_id):
    return bot.send_message(
        chat_id=chat_id,
        text="Welcome to the CSEC Updates announcement bot!",
        reply_markup = ReplyKeyboardMarkup(
            [["/groups", "/broadcast"], ["/admins", "/addadmin"]],
            resize_keyboard=True
        )
    )

def send_welcome_message(chat_id):
    return bot.send_message(
        chat_id=chat_id,
        text="Welcome to the CSEC Updates announcement bot!",
        reply_markup=ReplyKeyboardMarkup([["/Join our medias", "/Feedback", "/About us"]], resize_keyboard=True)
    )

def send_group_list(chat_id, groups):
    header = "<b>Here are the groups that I can forward messages to:</b>\n\n"
    if not groups:
        return bot.send_message(chat_id=chat_id, text="There are no groups to display.\n add me to groups you want to broadcast to")
    group_list = "\n".join([f"Title: {group['title']} | Username: @{group.get('username') if group.get('username') else 'Private Group'}" for group in groups]) 

    return bot.send_message(chat_id=chat_id, text=header + group_list, parse_mode="HTML")

def send_broadcast_prompt(chat_id):
    return bot.send_message(chat_id=chat_id, text="Please send me a message you want to broadcast or forward the message you want to broadcast from a channel in which I am an admin.")

def send_confirmation_prompt(user_id, chat_id, message_id): 
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data=f"forward:{chat_id}:{message_id}"),
            InlineKeyboardButton("No", callback_data="cancel-forward")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return bot.send_message(chat_id=user_id, text="Are you sure you want to send this message to all groups?", reply_markup=reply_markup)

async def send_admin_list_prompt(chat_id, admins):
    header = "<b>Here are the admins:</b>\n\n"
    admin_list = "\n".join([f"<i>Username: @{admin['username']}</i> - Name: <code>{admin.get('first_name', 'NA')}</code>" for admin in admins])
    formatted_message = header + admin_list
    await bot.send_message(chat_id=chat_id, text=formatted_message, parse_mode="HTML")
    
    
    
def is_private_message(webhook_data) -> bool:
    if webhook_data is None:
        return False

    message = webhook_data.message
    if message and message.get('chat'):
        return message['chat'].get('type') == "private"
    
    return False


def is_group_message(webhook_data) -> bool:
    if webhook_data is None:
        return False

    message = webhook_data.message
    if message and message.get('chat'):
        return message['chat'].get('type') in ["group", "supergroup"]
    return False

async def handle_reply(data):
    """Handles replies sent to the bot and forwards them to all admins."""
    try:
        if 'reply_to_message' in data.message:
            reply_message = data.message['reply_to_message']
            if 'id' in reply_message['from']:
                id = reply_message['from']['id']
                await bot.initialize()
                sent_count = 0
                if id == bot.id:
                    admins = get_admins()
                    
                    for admin in admins:
                        identifier = admin.get("id") or f"@{admin.get('username')}"
                        
                        if identifier:
                            try:
                                # Attempt to forward the message
                                sent_message = await bot.forward_message(
                                    chat_id=identifier,
                                    from_chat_id=data.message['chat']['id'],
                                    message_id=data.message['message_id']
                                )
                                sent_count += 1
                                
                                # await bot.send_message(
                                #     chat_id=identifier,
                                #     reply_to_message_id=sent_message.message_id,
                                #     text="this is forwarded message"
                                # )
                               
                               
                            except TelegramError as e:
                                pass
                                # Log the error for specific admin, but continue the loop
                                # await bot.send_message(
                                #     chat_id=data.message['chat']['id'],
                                #     text=f"Failed to forward message to {identifier}: {e}"
                                # )
                    if sent_count: 
                        
                        
                       
                    
                        keyboard = [
                            [InlineKeyboardButton("Give Feedback", url=f"https://t.me/{bot.username}")],
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        # Send the message with the inline keyboard
                        await bot.send_message(
                            chat_id=data.message['chat']['id'],
                            text=f"Hey {data.message['from']['first_name']}, You can send us a message using this link.",
                            reply_to_message_id=data.message['message_id'],
                            reply_markup=reply_markup
                        )
            
                                
    except Exception as e:
        pass
    return {"status": "ok"}


async def habdle_add_or_remove_group(data):
    group_data = data.message["chat"] 
    
    if 'left_chat_participant' in data.message:
        await bot.initialize()
        if bot.id == data.message['left_chat_participant']['id']:
            remove_group(group_data['id'])
    else:
        add_group(group_data)
            