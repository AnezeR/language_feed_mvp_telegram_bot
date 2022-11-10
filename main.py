import json
import sys
import time
from threading import Thread

import schedule

import telebot

from strings.strings import get_strings_for_user
from config.config import Config
from database.sqlitedb import Database
from layouts import page_layouts
from layouts.content_layout import LayoutType, ContentLayout
from content_sending import send_content_to_users
from initialize_database import check_if_database_exists

check_if_database_exists()

config = Config()
try:
    bot = telebot.TeleBot(config.telegram_bot_api_key)
except telebot.ExceptionHandler as e:
    print(f'Error connecting to the bot: {e}')
    sys.exit(1)

database = Database()


@bot.callback_query_handler(func=lambda call: True)
def inline_buttons_handling(call: telebot.types.CallbackQuery):
    data = json.loads(call.data)

    if data['type'] == LayoutType.content.value:
        layout = ContentLayout(
            strings=get_strings_for_user(database, call.from_user.id),
            content_id=data['content_id'],
            tg_user_id=call.from_user.id,
            bot=bot,
            db=database,
        )
        layout.handle_callback(call)


@bot.message_handler(func=lambda m: True)
def buttons_and_text_messages_handling(message: telebot.types.Message):
    if not database.user_exists(message.from_user.id):
        database.user_create(message.from_user.id)

        answer_layout = page_layouts.pick_layout(database.user_get_layout(message.from_user.id), message.from_user.id,
                                                 message.from_user.full_name, bot, database)
        bot.send_message(
            chat_id=message.chat.id,
            text=answer_layout.get_default_message(),
            reply_markup=answer_layout.get_keyboard_markup()
        )
        return

    answer_layout_id = database.user_get_layout(message.from_user.id)
    answer_layout = page_layouts.pick_layout(answer_layout_id, message.from_user.id, message.from_user.full_name, bot, database)
    answer, display_layout_id = answer_layout.reply_to_prompt(message)

    display_layout = page_layouts.pick_layout(display_layout_id, message.from_user.id, message.from_user.full_name, bot, database)
    database.user_set_layout(message.from_user.id, display_layout_id)
    bot.send_message(
        chat_id=message.chat.id,
        text=answer if answer else display_layout.get_default_message(),
        reply_markup=display_layout.get_keyboard_markup()
    )

    if answer_layout_id != display_layout_id:
        database.log_activity(message.from_user.id, "switch_page", {"start": answer_layout_id, "destination": display_layout_id})
    else:
        database.log_activity(message.from_user.id, "on_page_activity", {"message_text": message.text})


def pending_schedule():
    schedule.every().day.at(config.update_time).do(send_content_to_users, bot, database)
    while True:
        schedule.run_pending()
        time.sleep(1)


Thread(target=pending_schedule).start()

bot.infinity_polling()
