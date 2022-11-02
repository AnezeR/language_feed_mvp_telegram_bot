FROM archlinux:latest

WORKDIR /language_feed_bot

RUN pacman -Syu python cronie python-pip python-regex --noconfirm

RUN pip install pyTelegramBotApi strenum googletrans

COPY . .

RUN python3 /language_feed_bot/initialize_database.py

CMD python3 /language_feed_bot/actions_handler.py