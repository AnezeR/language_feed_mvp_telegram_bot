import json
import sys

import telebot

from strings.strings import get_strings_for_user
from config import Config
from database.sqlitedb import Database
from layouts import page_layouts
from layouts.content_layout import LayoutType, ContentLayout

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

        layout = page_layouts.pick_layout(database.user_get_layout(message.from_user.id), message.from_user.id,
                                          message.from_user.full_name, bot, database)
        bot.send_message(
            chat_id=message.chat.id,
            text=layout.get_default_message(),
            reply_markup=layout.get_keyboard_markup()
        )
        return

    layout = page_layouts.pick_layout(database.user_get_layout(message.from_user.id), message.from_user.id, message.from_user.full_name, bot, database)
    answer, layout_id = layout.reply_to_prompt(message)

    layout = page_layouts.pick_layout(layout_id, message.from_user.id, message.from_user.full_name, bot, database)
    database.user_set_layout(message.from_user.id, layout_id)
    bot.send_message(
        chat_id=message.chat.id,
        text=answer if answer else layout.get_default_message(),
        reply_markup=layout.get_keyboard_markup()
    )


bot.infinity_polling()

# todo: make the bot be able to run on different content
# todo: make a docker container for this bot

# todo: create questionnaires
# todo: improve landing

