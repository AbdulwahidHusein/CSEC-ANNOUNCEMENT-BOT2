from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.error import TelegramError
from config import TOKEN

bot = Bot(token=TOKEN)

def send_welcome_message(chat_id):
    return bot.send_message(
        chat_id=chat_id,
        text="Welcome to the CSEC Updates announcement bot!",
        reply_markup=ReplyKeyboardMarkup([["/groups", "/broadcast", "/admins", "/addadmin"]], resize_keyboard=True)
    )

def send_group_list(chat_id, groups):
    header = "<b>Here are the groups that I can forward messages to:</b>\n\n"
    group_list = "\n".join([f"<i>Title: {group['title']}</i> - Username: <code>@{group.get('username', 'NA')}</code>" for group in groups])
    return bot.send_message(chat_id=chat_id, text=header + group_list, parse_mode="HTML")

def send_broadcast_prompt(chat_id):
    return bot.send_message(chat_id=chat_id, text="Please send the message you want to broadcast.")

def send_confirmation_prompt(chat_id, message_id): 
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data=f"forward:{chat_id}:{message_id}"),
            InlineKeyboardButton("No", callback_data="cancel-forward")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return bot.send_message(chat_id=chat_id, text="Are you sure you want to send this message to all groups?", reply_markup=reply_markup)


async def send_admin_list_prompt(chat_id, admins):
    header = "<b>Here are the admins:</b>\n\n"
    admin_list = "\n".join([f"<i>Username: @{admin['username']}</i> - Name: <code>{admin.get('first_name', 'NA')}</code>" for admin in admins])
    formatted_message = header + admin_list
    await bot.send_message(chat_id=chat_id, text=formatted_message, parse_mode="HTML")

