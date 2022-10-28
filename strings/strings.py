import json

from db import Database


def get_strings_for_user(database: Database, tg_user_id: int) -> dict[str, str]:
    ui_language = database.get_language_for_user(tg_user_id)
    return json.load(open('strings/strings_en.json' if ui_language == 'English' else 'strings/strings_ru.json', 'r'))
