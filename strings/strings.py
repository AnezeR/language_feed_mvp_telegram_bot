import json

from database.sqlitedb import Database


def get_strings_for_user(database: Database, tg_user_id: int) -> dict[str, str]:
    ui_language = database.user_get_language(tg_user_id)
    return json.load(open('strings/strings_en.json' if ui_language == 'English' else 'strings/strings_ru.json', 'r'))
