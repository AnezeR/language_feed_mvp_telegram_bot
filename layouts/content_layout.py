import json
from enum import Enum

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telebot import TeleBot

from database.sqlitedb import Database


class LayoutType(Enum):
    preference = 'preference'
    content = 'content'
    translation = 'translation'
    questionnaire_link = 'questionnaire'


class Layout:
    def __init__(self, strings: dict[str, str]):
        self._inline_markup = InlineKeyboardMarkup()
        self._callback_data = {}
        self.strings = strings

    def handle_callback(self, call: CallbackQuery) -> None:
        pass

    def send_message(self) -> None:
        pass


# class QuestionnaireLayout(Layout):
#     def __init__(self, strings: dict[str, str], bot: TeleBot, db: Database, tg_user_id: int):
#         Layout.__init__(self, strings)
#
#         self.db = db
#         self.chat_id = tg_user_id
#         self.bot = bot
#
#         self._inline_markup.row(
#             InlineKeyboardButton(
#                 text=strings['questionnaire'],
#                 url='https://docs.google.com/forms/d/e/1FAIpQLSfnTk9cCK6MLlDJR7S-RK4rxkqNx7Lobd7N5Bd9h8OyYSAJwQ/viewform?usp=sharing',
#                 callback_data={'type': LayoutType.questionnaire_link.value}
#             )
#         )
#
#     def send_message(self) -> None:
#         self.bot.send_message(
#             self.chat_id,
#             self.strings['questionnaire_prompt'],
#             reply_markup=self._inline_markup
#         )
#
#     def handle_callback(self, call: CallbackQuery) -> None:
#

class NoButtonsContentLayout(Layout):
    def __init__(self, strings: dict[str, str], content_id: int, bot: TeleBot, db: Database, tg_user_id: int):
        Layout.__init__(self, strings)

        self.content_id = content_id
        self.db = db

        self.chat_id = tg_user_id
        self.bot = bot

    def send_message(self) -> None:
        val_type = self.db.content_get_val_type(self.content_id)
        if val_type == 'image':
            self.bot.send_photo(
                chat_id=self.chat_id,
                photo=self.db.content_get_file_id(self.content_id),
                reply_markup=self._inline_markup
            )
        elif val_type == 'video':
            self.bot.send_video(
                chat_id=self.chat_id,
                video=self.db.content_get_file_id(self.content_id),
                reply_markup=self._inline_markup
            )
        else:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=self.db.content_get_content(self.content_id),
                reply_markup=self._inline_markup
            )


class ContentLayout(NoButtonsContentLayout):
    def __init__(self, strings: dict[str, str], content_id: int, tg_user_id: int, bot: TeleBot, db: Database):
        NoButtonsContentLayout.__init__(self, strings, content_id, bot, db, tg_user_id)

        self.tg_user_id = tg_user_id

        self.liked = db.user_content_is_liked(tg_user_id, content_id)
        self.preference_name = self.db.content_get_preference_name(self.content_id)
        self.preference_description = self.db.preference_get_description(self.preference_name)
        self.is_test_content = not self.db.user_preference_is_liked(self.tg_user_id, self.preference_name)
        self._inline_markup.row(
            InlineKeyboardButton(
                self.strings['liked'] if self.liked else self.strings['not_liked'],
                callback_data=json.dumps(
                    {
                        'type': LayoutType.content.value,
                        'action': 'set_dislike' if self.liked else 'set_like',
                        'content_id': self.content_id
                    }
                )
            )
        )
        if self.liked and self.is_test_content:
            self._inline_markup.row(
                InlineKeyboardButton(
                    self.strings['see_more_of_this_content_1'] + self.preference_description + self.strings['see_more_of_this_content_2'],
                    callback_data=json.dumps(
                        {
                            'type': LayoutType.content.value,
                            'action': self.preference_name,
                            'content_id': self.content_id
                        }
                    )
                )
            )

    def handle_callback(self, call: CallbackQuery) -> None:
        # todo: refactor
        data = json.loads(call.data)

        if data['action'] in ('set_like', 'set_dislike'):
            action = data['action']
            liked_in_db = self.db.user_content_is_liked(self.tg_user_id, self.content_id)
            if action == 'set_like' and not liked_in_db:
                self.db.user_content_add_like(self.tg_user_id, self.content_id)
            elif action == 'set_dislike' and liked_in_db:
                self.db.user_content_remove_like(self.tg_user_id, self.content_id)

            self.db.log_activity(self.tg_user_id, action,
                                 {
                                     "content_id": self.content_id,
                                     "is_test_content": self.is_test_content
                                 })
        else:
            self.is_test_content = False
            self.db.user_preference_add_like(self.tg_user_id, self.preference_name)
            self.db.log_activity(self.tg_user_id, "add_like_preference",
                                 {
                                     "content_id": self.content_id,
                                     "preference_name": self.preference_name
                                 })

        self.liked = self.db.user_content_is_liked(self.tg_user_id, self.content_id)

        new_inline_markup = InlineKeyboardMarkup()
        new_inline_markup.row(
            InlineKeyboardButton(
                self.strings['liked'] if self.liked else self.strings['not_liked'],
                callback_data=json.dumps(
                    {
                        'type': LayoutType.content.value,
                        'action': 'set_dislike' if self.liked else 'set_like',
                        'content_id': self.content_id
                    }
                )
            )
        )
        if self.liked and self.is_test_content:
            new_inline_markup.row(
                InlineKeyboardButton(
                    self.strings['see_more_of_this_content_1'] + self.preference_description + self.strings['see_more_of_this_content_2'],
                    callback_data=json.dumps(
                        {
                            'type': LayoutType.content.value,
                            'action': self.preference_name,
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
