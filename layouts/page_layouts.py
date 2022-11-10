from googletrans import Translator
from telebot.types import ReplyKeyboardMarkup, Message

from content_sending import *
from database.sqlitedb import Language
from layouts.page_layout_ids import *
from strings.strings import get_strings_for_user


def translate_text(text: str) -> str:
    trans = Translator()
    return trans.translate(text, dest='en' if trans.detect(text).lang == 'ru' else 'ru').text


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
        return translate_text(message.text), first_settings


class MainMenuLayout(Layout):
    def __init__(self, strings: dict[str, str], name: str, bot: TeleBot, database: Database):
        Layout.__init__(self, strings)

        self.tg_user_name = name

        self.bot = bot
        self.database = database

        self._default_message = self.strings['main_menu_thing'] + (f', {self.tg_user_name}!' if self.tg_user_name != '' else '')

        self._keyboard_markup.row(self.strings['feed_for_today'])
        self._keyboard_markup.row(self.strings['settings'], self.strings['likes'])

    def reply_to_prompt(self, message: Message) -> tuple[str, int]:
        if message.text == self.strings['feed_for_today']:
            send_daily_content_for_user(
                self.strings,
                bot=self.bot,
                db=self.database,
                tg_user_id=message.from_user.id,
            )
            return self.strings['feed_for_today_thing'] + (f', {self.tg_user_name}!' if self.tg_user_name != '' else ''), main_menu
        elif message.text == self.strings['likes']:
            self.database.user_likes_buffer(message.from_user.id)
            if self.database.user_likes_get_buffered_likes_count(message.from_user.id):
                send_likes_for_user(
                    self.strings,
                    bot=self.bot,
                    db=self.database,
                    tg_user_id=message.from_user.id
                )
                return '', look_at_likes
            else:
                return self.strings['no_likes'], main_menu
        elif message.text == self.strings['settings']:
            return '', settings

        return translate_text(message.text), main_menu


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
        return translate_text(message.text), settings


class ChoosingPreferencesLayout(Layout):
    def __init__(self, strings: dict[str, str], tg_user_id: int, bot: TeleBot, database: Database):
        Layout.__init__(self, strings)

        self.bot = bot
        self.database = database

        self.first_time = self.database.user_get_day_of_feed(tg_user_id) == 0

        self._default_message = self.strings['choose_your_preferences']

        if self.first_time:
            self._keyboard_markup.row(self.strings['finish_setting_preferences'])
        else:
            self._keyboard_markup.row(self.strings['return_to_settings'])
        for preference in self.database.preference_get_all_preferences():
            like_button = self.strings['liked'] if self.database.user_preference_is_liked(tg_user_id, preference) else self.strings['not_liked']
            self._keyboard_markup.row(self.database.preference_get_description(preference) + f' {like_button}')

    def reply_to_prompt(self, message: Message) -> tuple[str, int]:
        preferences_are_set = self.database.user_preferences_are_set(message.from_user.id)
        if self.first_time and message.text == self.strings['finish_setting_preferences']:
            if preferences_are_set:
                self.database.user_increase_day_of_feed(message.from_user.id)
                send_daily_content_for_user(self.strings, self.bot, self.database, message.from_user.id)
                return '', main_menu
            else:
                return self.strings['choose_your_preferences'], choosing_preferences
        if (not self.first_time) and message.text == self.strings['return_to_settings']:
            if preferences_are_set:
                return '', settings
            else:
                return self.strings['choose_your_preferences'], choosing_preferences

        for preference in self.database.preference_get_all_preferences():
            preference_liked = self.database.user_preference_is_liked(message.from_user.id, preference)
            like_button = self.strings['liked'] if preference_liked else self.strings['not_liked']
            check_string = self.database.preference_get_description(preference) + ' ' + like_button

            if message.text == check_string:
                self.database.user_set_looking_at_preference(message.from_user.id, preference)
                send_test_content_for_preference(self.strings, self.bot, self.database, message.from_user.id,
                                                 preference)
                return '', look_at_content
        return translate_text(message.text), choosing_preferences


class LookAtPreferenceLayout(Layout):
    def __init__(self, strings: dict[str, str], tg_user_id: int, database: Database):
        Layout.__init__(self, strings)

        self.database = database
        self.preference = self.database.user_get_looking_at_preference(tg_user_id)

        liked = self.database.user_preference_is_liked(tg_user_id, self.preference)

        if liked:
            self._default_message = self.strings['you_do_like_this_type_of_content']
        else:
            self._default_message = self.strings['do_you_like_this_type_of_content']

        self._keyboard_markup.row(self.strings['look_at_other_content'], self.strings['liked'] if liked else self.strings['not_liked'])

    def reply_to_prompt(self, message: Message) -> tuple[str, int]:
        if message.text == self.strings['look_at_other_content']:
            self.database.user_set_looking_at_preference(message.from_user.id, None)
            return '', choosing_preferences
        if message.text == self.strings['liked']:
            self.database.user_preference_remove_like(message.from_user.id, self.preference)
            self.database.log_activity(message.from_user.id, "remove_like_preference",
                                       {
                                           "content_id": None,
                                           "preference_name": self.preference,
                                       })
            return '', look_at_content
        if message.text == self.strings['not_liked']:
            self.database.log_activity(message.from_user.id, "add_like_preference",
                                       {
                                           "content_id": None,
                                           "preference_name": self.preference,
                                       })
            self.database.user_preference_add_like(message.from_user.id, self.preference)
            return '', look_at_content
        return translate_text(message.text), look_at_content


class ChoosingLanguageLayout(Layout):
    def __init__(self, strings: dict[str, str], tg_user_id: int, database: Database):
        Layout.__init__(self, strings)

        self.database = database
        self.first_time = self.database.user_get_day_of_feed(tg_user_id) == 0

        self._default_message = self.strings['choose_the_language']
        for language in Language:
            self._keyboard_markup.row(language)

    def reply_to_prompt(self, message: Message) -> tuple[str, int]:
        for language in Language:
            if message.text == language:
                self.database.user_set_language(message.from_user.id, language)
                return get_strings_for_user(self.database, message.from_user.id)['langauge_is_set_to'] + language, choosing_preferences if self.first_time else settings
        return translate_text(message.text), choosing_language


class LookingAtLikesLayout(Layout):
    def __init__(self, strings: dict[str, str], tg_user_id: int, full_name: str, bot: TeleBot, database: Database):
        Layout.__init__(self, strings)

        self.database = database
        self.bot = bot

        number_of_likes = self.database.user_likes_get_buffered_likes_count(tg_user_id)
        self.current_page = self.database.user_likes_get_current_page(tg_user_id)

        self._keyboard_markup.row(self.strings['return_to_the_main_menu'])

        if number_of_likes:
            self._default_message = self.strings['here_are_your_likes'] + full_name

            beginning = self.current_page * 3
            end = beginning + 3

            if beginning > 0 and end < number_of_likes:
                self._keyboard_markup.row(self.strings['previous_page'], self.strings['next_page'])
            elif beginning > 0:
                self._keyboard_markup.row(self.strings['previous_page'])
            elif end < number_of_likes:
                self._keyboard_markup.row(self.strings['next_page'])
        else:
            self._default_message = self.strings['no_likes']

    def reply_to_prompt(self, message: Message) -> tuple[str, int]:
        if message.text == self.strings['return_to_the_main_menu']:
            self.database.user_likes_set_current_page(message.from_user.id, 0)
            self.database.user_likes_delete_buffer(message.from_user.id)
            return '', main_menu
        if message.text == self.strings['next_page']:
            self.database.user_likes_set_current_page(message.from_user.id, self.current_page + 1)
            send_likes_for_user(
                strings=self.strings,
                bot=self.bot,
                db=self.database,
                tg_user_id=message.from_user.id
            )
            return '', look_at_likes
        if message.text == self.strings['previous_page']:
            self.database.user_likes_set_current_page(message.from_user.id, self.current_page - 1)
            send_likes_for_user(
                strings=self.strings,
                bot=self.bot,
                db=self.database,
                tg_user_id=message.from_user.id
            )
            return '', look_at_likes
        return translate_text(message.text), look_at_likes


def pick_layout(layout_id: int, tg_user_id: int, full_name: str, bot: TeleBot, database: Database) -> Layout:
    strings = get_strings_for_user(database, tg_user_id)

    if layout_id == first_settings:
        return FirstSettingsLayout(strings)
    if layout_id == main_menu:
        return MainMenuLayout(strings, full_name, bot, database)
    if layout_id == settings:
        return SettingsLayout(strings, full_name, bot, database)
    if layout_id == choosing_language:
        return ChoosingLanguageLayout(strings, tg_user_id, database)
    if layout_id == choosing_preferences:
        return ChoosingPreferencesLayout(strings, tg_user_id, bot, database)
    if layout_id == look_at_content:
        return LookAtPreferenceLayout(strings, tg_user_id, database)
    if layout_id == look_at_likes:
        return LookingAtLikesLayout(strings, tg_user_id, full_name, bot, database)

    return MainMenuLayout(strings, full_name, bot, database)
