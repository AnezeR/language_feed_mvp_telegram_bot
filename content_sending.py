import random

from telebot import TeleBot

from database.sqlitedb import Database
from layouts.content_layout import ContentLayout, NoButtonsContentLayout
from strings.strings import get_strings_for_user


def __send_daily_feed(strings: dict[str, str], bot: TeleBot, db: Database, tg_user_id: int) -> None:
    from layouts.page_layouts import pick_layout
    send_daily_content_for_user(strings, bot, db, tg_user_id)
    if db.user_get_day_of_feed(tg_user_id) == 7:
        bot.send_message(tg_user_id, strings['final_message'])
    else:
        layout = pick_layout(db.user_get_layout(tg_user_id), tg_user_id, "", bot, db)
        bot.send_message(tg_user_id, strings['feed_for_today_thing'], reply_markup=layout.get_keyboard_markup())


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


def send_questionnaires(strings: dict[str, str], bot: TeleBot, db: Database, tg_user_id: int) -> None:
    pass


def send_likes_for_user(strings: dict[str, str], bot: TeleBot, db: Database, tg_user_id: int) -> None:
    for content_id in db.user_likes_get_content_for_current_page(tg_user_id)[::-1]:
        ContentLayout(strings, content_id, tg_user_id, bot, db).send_message()


def send_test_content_for_preference(strings: dict[str, str], bot: TeleBot, db: Database, tg_user_id: int, preference_name: str) -> None:
    for content_id in db.preference_get_content_for_day(preference_name, 0):
        NoButtonsContentLayout(strings, content_id, bot, db, tg_user_id).send_message()


def send_content_to_users(bot: TeleBot, database: Database):

    for tg_user_id in database.user_get_all_users():
        try:
            if database.user_get_day_of_feed(tg_user_id) < 7:
                database.user_increase_day_of_feed(tg_user_id)
                strings = get_strings_for_user(database, tg_user_id)
                __send_daily_feed(strings, bot, database, tg_user_id)
        except Exception:
            continue
