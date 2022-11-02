import random

from telebot import TeleBot

from config import Config
from database.sqlitedb import Database
from layouts.content_layout import ContentLayout, NoButtonsContentLayout
from strings.strings import get_strings_for_user


def send_daily_content_for_user(strings: dict[str, str], bot: TeleBot, db: Database, tg_user_id: int) -> None:
    day = db.user_get_day_of_feed(tg_user_id)

    content_to_send = list[int]()
    for preference in db.preference_get_all_preferences():
        content = db.preference_get_content_for_day(preference, day)
        if db.user_preference_is_liked(tg_user_id, preference):
            content_to_send += content
        else:
            content_to_send += random.sample(content, 1)

    random.shuffle(content_to_send)
    for content_id in content_to_send:
        ContentLayout(strings, content_id, tg_user_id, bot, db).send_message()


def send_likes_for_user(strings: dict[str, str], bot: TeleBot, db: Database, tg_user_id: int) -> None:
    for content_id in db.user_likes_get_content_for_current_page(tg_user_id)[::-1]:
        ContentLayout(strings, content_id, tg_user_id, bot, db).send_message()


def send_test_content_for_preference(strings: dict[str, str], bot: TeleBot, db: Database, tg_user_id: int, preference_name: str) -> None:
    for content_id in db.preference_get_content_for_day(preference_name, 0):
        NoButtonsContentLayout(strings, content_id, bot, db, tg_user_id).send_message()


if __name__ == '__main__':
    config = Config()
    __bot = TeleBot(config.telegram_bot_api_key)
    __database = Database()

    for __tg_user_id in __database.user_get_all_users():
        try:
            __strings = get_strings_for_user(__database, __tg_user_id)
            send_daily_content_for_user(__strings, __bot, __database, __tg_user_id)
            __database.user_increase_day_of_feed(__tg_user_id)
        except Exception:
            continue
