from googletrans import Translator
from telebot.types import ReplyKeyboardMarkup, Message

import db
from content_sending import *
from layouts.page_layout_ids import *
from preload import ContentPreload
from strings.strings import get_strings_for_user


class Layout:

    def __init__(self, strings: dict[str, str]):
        self._default_message = ''
        self._keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        self.strings = strings

    def reply_to_prompt(self, message: Message) -> tuple[str, int]:
        pass

    def get_default_message(self) -> str:
        return self._default_message

    def get_keyboard_markup(self) -> ReplyKeyboardMarkup:
        return self._keyboard_markup


class FirstSettingsLayout(Layout):
    def __init__(self, strings: dict[str, str]):
        Layout.__init__(self, strings)
        self._default_message = self.strings['guide']
        self._keyboard_markup.row(self.strings['set_preferences'])

    def reply_to_prompt(self, message: Message) -> tuple[str, int]:
        if message.text == self.strings['set_preferences']:
            return '', choosing_language


class MainMenuLayout(Layout):
    def __init__(self, strings: dict[str, str], name: str, bot: TeleBot, database: Database, preload: ContentPreload):
        Layout.__init__(self, strings)

        self.tg_user_name = name

        self.bot = bot
        self.database = database
        self.preload = preload

        self._default_message = self.strings['main_menu_thing'] + f'{self.tg_user_name}!'

        self._keyboard_markup.row(self.strings['feed_for_today'])
        self._keyboard_markup.row(self.strings['settings'], self.strings['likes'])

    def reply_to_prompt(self, message: Message) -> tuple[str, int]:
        if message.text == self.strings['feed_for_today']:
            send_daily_content_for_user(
                bot=self.bot,
                db=self.database,
                tg_user_id=message.from_user.id,
                preload=self.preload
            )
            return self.strings['feed_for_today_thing'] + self.tg_user_name, main_menu
        elif message.text == self.strings['likes']:
            send_likes_for_user(
                bot=self.bot,
                db=self.database,
                tg_user_id=message.from_user.id,
                preload=self.preload
            )
            return self.strings['likes_thing'] + self.tg_user_name, main_menu
        elif message.text == self.strings['settings']:
            return '', settings

        return Translator().translate(message.text, dest='ru').text, main_menu


class SettingsLayout(Layout):
    def __init__(self, strings: dict[str, str], tg_user_name: str, bot: TeleBot, database: Database):
        Layout.__init__(self, strings)

        self.bot = bot
        self.database = database

        self._default_message = self.strings['setting_page_thing'] + f'{tg_user_name}!'

        self._keyboard_markup.row(self.strings['return_to_the_main_menu'])
        self._keyboard_markup.row(self.strings['language'], self.strings['preferences'])

    def reply_to_prompt(self, message: Message) -> tuple[str, int]:
        if message.text == self.strings['return_to_the_main_menu']:
            return '', main_menu
        elif message.text == self.strings['language']:
            return '', choosing_language
            pass
        elif message.text == self.strings['preferences']:
            return '', choosing_preferences
        return Translator().translate(message.text, dest='ru').text, settings


class ChoosingPreferencesLayout(Layout):
    def __init__(self, strings: dict[str, str], tg_user_id: int, bot: TeleBot, database: Database, preload: ContentPreload):
        Layout.__init__(self, strings)

        self.bot = bot
        self.database = database
        self.preload = preload

        self.first_time = self.database.are_preferences_not_set(tg_user_id)

        self._default_message = self.strings['choose_your_preferences']

        if self.first_time:
            self._keyboard_markup.row(self.strings['finish_setting_preferences'])
        else:
            self._keyboard_markup.row(self.strings['return_to_settings'])
        for preference in self.database.get_content_types():
            like_button = self.strings['liked'] if self.database.is_content_type_liked_by_user(tg_user_id, preference) else self.strings['not_liked']
            self._keyboard_markup.row(preference + f' {like_button}')

    def reply_to_prompt(self, message: Message) -> tuple[str, int]:
        if not self.database.are_there_zero_preferences(message.from_user.id):
            if self.first_time and message.text == self.strings['finish_setting_preferences']:
                self.database.end_setting_preferences_and_set_first_day(message.from_user.id)
                send_daily_content_for_user(self.bot, self.database, self.preload, message.from_user.id)
                return '', main_menu
            if (not self.first_time) and message.text == self.strings['return_to_settings']:
                return '', settings

        for preference in self.database.get_content_types():
            preference_liked = self.database.is_content_type_liked_by_user(message.from_user.id, preference)
            like_button = self.strings['liked'] if preference_liked else self.strings['not_liked']
            check_string = preference + ' ' + like_button

            if message.text == check_string:
                self.database.set_user_looking_at_content_type(message.from_user.id, preference)
                send_test_content_for_content_type(self.bot, self.database, self.preload, message.from_user.id, preference)
                return '', look_at_content
        return Translator().translate(message.text, dest='ru').text, choosing_preferences


class LookAtContentLayout(Layout):
    def __init__(self, strings: dict[str, str], tg_user_id: int, database: Database):
        Layout.__init__(self, strings)

        self.database = database
        self.content_type = self.database.get_content_type_user_is_looking_at(tg_user_id)

        liked = self.database.is_content_type_liked_by_user(tg_user_id, self.content_type)

        if liked:
            self._default_message = self.strings['you_do_like_this_type_of_content']
        else:
            self._default_message = self.strings['do_you_like_this_type_of_content']

        self._keyboard_markup.row(self.strings['look_at_other_content'], self.strings['liked'] if liked else self.strings['not_liked'])

    def reply_to_prompt(self, message: Message) -> tuple[str, int]:
        if message.text == self.strings['look_at_other_content']:
            self.database.set_user_looking_at_content_type(message.from_user.id, None)
            return '', choosing_preferences
        if message.text == self.strings['liked']:
            self.database.remove_like_a_content_type_for_user(message.from_user.id, self.content_type)
            return '', look_at_content
        if message.text == self.strings['not_liked']:
            self.database.like_a_content_type_for_user(message.from_user.id, self.content_type)
            return '', look_at_content
        return Translator().translate(message.text, dest='ru').text, look_at_content


class ChoosingLanguageLayout(Layout):
    def __init__(self, strings: dict[str, str], tg_user_id: int, database: Database):
        Layout.__init__(self, strings)

        self.database = database
        self.first_time = self.database.are_preferences_not_set(tg_user_id)

        self._default_message = self.strings['choose_the_language']
        for language in db.Language:
            self._keyboard_markup.row(language)

    def reply_to_prompt(self, message: Message) -> tuple[str, int]:
        for language in db.Language:
            if message.text == language:
                self.database.set_language_for_user(message.from_user.id, language)
                return get_strings_for_user(self.database, message.from_user.id)['langauge_is_set_to']+language, choosing_preferences if self.first_time else settings
        return '', choosing_language


class LookingAtLikesLayout(Layout):
    def __init__(self, strings: dict[str, str], tg_user_id: int, bot: TeleBot, database: Database, preload: ContentPreload):
        Layout.__init__(self, strings)

        self.database = database
        self.bot = bot
        self.preload = preload

        user_likes = self.database.get_likes_for_user(tg_user_id)
        current_page = self.database.get_current_likes_page_for_user(tg_user_id)

        if user_likes:
            self._default_message = self.strings['here_are_your_likes']  # todo: add likes messages to strings
            self._keyboard_markup.row(self.strings['return_to_the_main_menu'])

            beginning = current_page * 5
            end = beginning + 5

            if beginning > 0:
                self._keyboard_markup.add(self.strings['previous_page'])  # todo: add previous page to strings
            if end < len(user_likes):
                self._keyboard_markup.add(self.strings['next_page'])  # todo: add next page to strings



        else:
            self._default_message = self.strings['no_likes']  # todo: add no likes messages to strings

    def reply_to_prompt(self, message: Message) -> tuple[str, int]:
        pass  # todo: finish replying to prompt with likes

def pick_layout(layout_id: int, tg_user_id: int, full_name: str, bot: TeleBot, database: Database, preload: ContentPreload) -> Layout:
    strings = get_strings_for_user(database, tg_user_id)

    if layout_id == first_settings:
        return FirstSettingsLayout(strings)
    if layout_id == main_menu:
        return MainMenuLayout(strings, full_name, bot, database, preload)
    if layout_id == settings:
        return SettingsLayout(strings, full_name, bot, database)
    if layout_id == choosing_language:
        return ChoosingLanguageLayout(strings, tg_user_id, database)
    if layout_id == choosing_preferences:
        return ChoosingPreferencesLayout(strings, tg_user_id, bot, database, preload)
    if layout_id == look_at_content:
        return LookAtContentLayout(strings, tg_user_id, database)

    return MainMenuLayout(strings, full_name, bot, database, preload)
