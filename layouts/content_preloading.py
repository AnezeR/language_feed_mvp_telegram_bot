import telebot


class ContentPreloader:
    def __init__(self, bot: telebot.TeleBot, chat_id_to_preload: str):
        self.__bot = bot
        self.__chat_id_to_preload = chat_id_to_preload
        self.__content = dict[int, str]()

    def preload_content(self, content_ids: list[int]):
        pass

    def get_content(self, content_id: int) -> str:
        return self.__content[content_id]
