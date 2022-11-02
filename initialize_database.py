import os
import re
from pathlib import Path

import telebot

from config import Config
from database.sqlitedb import Database
from concurrent.futures import ThreadPoolExecutor

"""Getting path to the script directory for further use in commands and loading files"""
path_to_script_dir = Path(os.path.dirname(os.path.abspath(__file__)))

"""Getting config and database"""
database = Database()
database.execute_init_script()
config = Config()

"""Adding content to the database"""


def get_val_type(type_str) -> str:
    if type_str in ('png', 'jpg', 'gif'):
        return 'image'
    return 'video'


def handle_one_item(item_path: Path, content_type: str):
    res = re.search(r'day_([0-9])_[0-9]\.(.*)$', str(item_path))
    database.content_add_content(content_type, content=str(item_path), day=res[1], val_type=get_val_type(res[2]))


def handle_content_type(content_type: str):
    path_to_content_dir = path_to_script_dir / config.current_content / content_type
    database.preference_add_preference(content_type, open(path_to_content_dir / 'description', 'r').read())
    for filename in os.listdir(path_to_script_dir / config.current_content / content_type):
        if filename == 'description':
            continue
        handle_one_item(path_to_content_dir / filename, content_type)


def add_content_types():
    for filename in os.listdir(path_to_script_dir / config.current_content):
        handle_content_type(filename)


add_content_types()

"""Preloading added content"""

preloaded_content = dict[int, str]()

bot = telebot.TeleBot(config.telegram_bot_api_key)
chat_id_for_cache = config.admin_chat_id


def preload_content(info: tuple[int, str, str]) -> None:
    c_id, content, val_type = info
    if val_type == 'image':
        photo = open(content, 'rb')
        message_for_cache = bot.send_photo(
            chat_id=chat_id_for_cache,
            photo=photo
        )
        preloaded_content[c_id] = message_for_cache.photo[0].file_id
    if val_type == 'video':
        video = open(content, 'rb')
        message_for_cache = bot.send_video(
            chat_id=chat_id_for_cache,
            video=video
        )
        preloaded_content[c_id] = message_for_cache.video.file_id


preload_prerequisites = [(content_id, database.content_get_content(content_id), database.content_get_val_type(content_id)) for content_id in database.content_get_ids_to_preload()]


with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(preload_content, preload_prerequisites)

for content_id, file_id in preloaded_content.items():
    database.content_set_file_id(content_id, file_id)

database.close()
