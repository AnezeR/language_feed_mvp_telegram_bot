from telebot import TeleBot

from config import Config
from db import Database
from layouts.content_layout import ContentLayout, NoButtonsContentLayout
from preload import ContentPreload
from strings.strings import get_strings_for_user


def send_daily_content_for_user(strings: dict[str, str], bot: TeleBot, db: Database, preload: ContentPreload, tg_user_id: int) -> None:
    for content_id in db.get_additional_content_for_user(tg_user_id) + db.get_content_for_user(tg_user_id):
        layout = ContentLayout(
            strings=strings,
            content_id=content_id,
            tg_user_id=tg_user_id,
            bot=bot,
            db=db,
            preload=preload
        )
        layout.send_message()


def send_likes_for_user(strings: dict[str, str], bot: TeleBot, db: Database, preload: ContentPreload, tg_user_id: int) -> None:
    for content_id in db.get_likes_for_current_page(tg_user_id)[::-1]:
        layout = ContentLayout(
            strings=strings,
            content_id=content_id,
            tg_user_id=tg_user_id,
            bot=bot,
            db=db,
            preload=preload
        )
        layout.send_message()


def send_test_content_for_content_type(strings: dict[str, str], bot: TeleBot, db: Database, preload: ContentPreload, tg_user_id: int, content_type: str) -> None:
    for content_id in db.get_test_content_for_content_type(content_type):
        layout = NoButtonsContentLayout(
            strings=strings,
            content_id=content_id,
            tg_user_id=tg_user_id,
            bot=bot,
            db=db,
            preload=preload
        )
        layout.send_message()


if __name__ == '__main__':
    config = Config()
    __bot = TeleBot(config.telegram_bot_api_key)
    __database = Database(user=config.mariadb_user, password=config.mariadb_password, database=config.mariadb_database)
    __preload = ContentPreload(__database, __bot, config.admin_chat_id)

    for __tg_user_id in __database.get_all_users():
        try:
            __strings = get_strings_for_user(__database, __tg_user_id)
            send_daily_content_for_user(__strings, __bot, __database, __preload, __tg_user_id)
            __database.increase_feed_day_for_user(__tg_user_id)
        except Exception:
            continue
