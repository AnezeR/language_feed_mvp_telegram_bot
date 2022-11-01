import json
import sys

import telebot

from preload import ContentPreload
from config import Config
from db import Database
from layouts import page_layouts
from layouts.content_layout import ContentLayout, LayoutType

config = Config()
try:
    bot = telebot.TeleBot(config.telegram_bot_api_key)
except telebot.ExceptionHandler as e:
    print(f'Error connecting to the bot: {e}')
    sys.exit(1)

database = Database(user=config.mariadb_user, password=config.mariadb_password, database=config.mariadb_database)
preloaded_content = ContentPreload(database, bot, config.admin_chat_id)


@bot.callback_query_handler(func=lambda call: True)
def inline_buttons_handling(call: telebot.types.CallbackQuery):
    data = json.loads(call.data)

    if data['type'] == LayoutType.content.value:
        layout = ContentLayout(
            content_id=data['content_id'],
            tg_user_id=call.from_user.id,
            bot=bot,
            db=database,
            preload=preloaded_content
        )
        layout.handle_callback(call)


@bot.message_handler(func=lambda m: True)
def buttons_and_text_messages_handling(message: telebot.types.Message):
    if not database.user_exists(message.from_user.id):
        database.create_user(message.from_user.id)

        layout = page_layouts.pick_layout(database.get_user_layout(message.from_user.id), message.from_user.id,
                                          message.from_user.full_name, bot, database, preloaded_content)
        bot.send_message(
            chat_id=message.chat.id,
            text=layout.get_default_message(),
            reply_markup=layout.get_keyboard_markup()
        )
        return

    layout = page_layouts.pick_layout(database.get_user_layout(message.from_user.id), message.from_user.id, message.from_user.full_name, bot, database, preloaded_content)
    answer, layout_id = layout.reply_to_prompt(message)

    layout = page_layouts.pick_layout(layout_id, message.from_user.id, message.from_user.full_name, bot, database, preloaded_content)
    database.set_user_layout(message.from_user.id, layout_id)
    bot.send_message(
        chat_id=message.chat.id,
        text=answer if answer else layout.get_default_message(),
        reply_markup=layout.get_keyboard_markup()
    )


bot.infinity_polling()

# todo: give random content to users with daily feed
# todo: create questionnaires
# todo: improve landing
# todo: switch database to sqlite and merge preloading with database
