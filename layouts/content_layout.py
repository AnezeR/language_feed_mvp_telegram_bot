import json
from enum import Enum

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telebot import TeleBot

from db import Database
from preload import ContentPreload


class LayoutType(Enum):
    preference = 'preference'
    content = 'content'
    translation = 'translation'


class Layout:
    def __init__(self):
        self._inline_markup = InlineKeyboardMarkup()
        self._callback_data = {}

    def handle_callback(self, call: CallbackQuery) -> None:
        pass

    def send_message(self) -> None:
        pass


class NoButtonsContentLayout(Layout):
    def __init__(self, content_id: int, bot: TeleBot, db: Database, tg_user_id: int, preload: ContentPreload):
        Layout.__init__(self)

        self.content_id = content_id
        self.db = db

        self.chat_id = tg_user_id
        self.bot = bot

        self.preload = preload

    def send_message(self) -> None:
        val_type = self.db.get_value_type_of_content(self.content_id)
        if val_type == 'image':
            self.bot.send_photo(
                chat_id=self.chat_id,
                photo=self.preload.get_file_id_for_content_id(self.content_id),
                reply_markup=self._inline_markup
            )
        elif val_type == 'video':
            self.bot.send_video(
                chat_id=self.chat_id,
                video=self.preload.get_file_id_for_content_id(self.content_id),
                reply_markup=self._inline_markup
            )
        else:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=self.db.get_content_content(self.content_id),
                reply_markup=self._inline_markup
            )


class ContentLayout(NoButtonsContentLayout):
    def __init__(self, content_id: int, tg_user_id: int, bot: TeleBot, db: Database, preload: ContentPreload):
        NoButtonsContentLayout.__init__(self, content_id, bot, db, tg_user_id, preload)

        self.tg_user_id = tg_user_id

        self.liked = db.is_content_liked_by_user(tg_user_id, content_id)
        self._inline_markup.row(
            InlineKeyboardButton(
                '❤️' if self.liked else '🤍',
                callback_data=json.dumps(
                    {
                        'type': LayoutType.content.value,
                        'val': '❤️' if self.liked else '🤍',
                        'content_id': self.content_id
                    }
                )
            )
        )

    def handle_callback(self, call: CallbackQuery) -> None:
        data = json.loads(call.data)

        liked = data['val'] == '🤍'
        liked_in_db = self.db.is_content_liked_by_user(self.tg_user_id, self.content_id)

        if liked != liked_in_db:
            if liked:
                self.db.set_like_for_user(self.tg_user_id, self.content_id)
            else:
                self.db.remove_like_for_user(self.tg_user_id, self.content_id)

            action = '❤' if liked else '🤍'
            new_inline_markup = InlineKeyboardMarkup()
            new_inline_markup.row(
                InlineKeyboardButton(
                    action,
                    callback_data=json.dumps(
                        {
                            'type': LayoutType.content.value,
                            'val': action,
                            'content_id': self.content_id
                        }
                    )
                )
            )
            self.bot.edit_message_reply_markup(
                chat_id=self.chat_id,
                message_id=call.message.id,
                reply_markup=new_inline_markup
            )
