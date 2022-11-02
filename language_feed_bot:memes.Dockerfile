FROM python:3.10-slim-buster

WORKDIR /language_feed_bot

RUN pip install pyTelegramBotApi strenum googletrans==3.1.0a0 schedule

COPY . .

RUN python /language_feed_bot/initialize_database.py

CMD ["python3", "/language_feed_bot/actions_handler.py"]