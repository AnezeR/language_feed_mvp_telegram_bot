from telebot import TeleBot

from db import Database


class ContentPreload:

    def __init__(self, db: Database, bot: TeleBot, chat_id_for_cache: int):
        self.preloaded_content = dict[int, str]()

        for content_id in db.get_content_ids_to_preload():
            val_type = db.get_value_type_of_content(content_id)
            if val_type == 'image':
                photo = open(db.get_content_content(content_id), 'rb')
                message_for_cache = bot.send_photo(
                    chat_id=chat_id_for_cache,
                    photo=photo
                )
                self.preloaded_content[content_id] = message_for_cache.photo[0].file_id
            if val_type == 'video':
                video = open(db.get_content_content(content_id), 'rb')
                message_for_cache = bot.send_video(
                    chat_id=chat_id_for_cache,
                    video=video
                )
                self.preloaded_content[content_id] = message_for_cache.video.file_id

    def get_file_id_for_content_id(self, content_id: int) -> str:
        return self.preloaded_content[content_id]
