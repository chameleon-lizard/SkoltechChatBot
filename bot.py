import logging
import re
import os

import time

import dotenv
import telebot

from main import Chatbot
from src.db import BotDB


def format_for_telegram(text: str) -> str:
    return (
        text.replace("*", "\*")
        .replace("~", "\~")
        .replace("`", "\`")
        .replace(">", "\>")
        .replace("#", "\#")
        .replace("|", "\|")
        .replace("{", "\{")
        .replace("}", "\}")
    )


logging.basicConfig(
    format='[%(threadName)s] %(levelname)s: %(message)s"', level=logging.INFO
)

dotenv.load_dotenv("env")

time.sleep(30)  # Waiting for postgres to load

db = BotDB(
    db_name=f"{os.environ.get('POSTGRES_DB')}",
    db_user=f"{os.environ.get('POSTGRES_USER')}",
    db_password=f"{os.environ.get('POSTGRES_PASSWORD')}",
    host="db",
    port="5432",
    bot_id=6708881992,
    bot_username="@CyberBorisBot",
    bot_email="cyberboris@skoltech.ru",
)

bot = telebot.TeleBot(
    token=f"{os.environ.get('BOT_TOKEN')}",
    parse_mode="MARKDOWN",
    threaded=True,
)


c = Chatbot(
    f"{os.environ.get('CHATBOT_MODEL')}",
    f"{os.environ.get('API_LINK')}",
    f"{os.environ.get('VSEGPT_TOKEN')}",
    ["data/orientation.md"],
)
c.build_database()


@bot.message_handler(func=lambda message: message.text in ("/start", "/help", "Help"))
def welcome(message: telebot.types.Message) -> None:
    """
    Handle the user's first message to the bot, sending a greeting and instructions on how to use the bot.

    :param message: The message object received from the user.

    :return: None
    """
    db.add_user(message.chat.id, message.from_user.username)

    db.add_message(
        message.id,
        message.chat.id,
        message.text,
        (message.reply_to_message.id if message.reply_to_message is not None else None),
    )

    # Replying with welcome message
    bot.reply_to(
        message=message,
        text="Hi there! My name is CyberBoris and I am a kinda smart bot, which can answer questions about Skoltech. Please, tell me your Skoltech email so we can continue.",
    )


def check_email(message: telebot.types.Message) -> None:
    db.add_message(
        message.id,
        message.chat.id,
        message.text,
        (message.reply_to_message.id if message.reply_to_message is not None else None),
    )

    bot.reply_to(
        message=message, text="Check your email and please send me the code ;)"
    )

    db.authorize_user(message.chat.id, message.text)


@bot.message_handler(content_types=["text"])
def send_question(message: telebot.types.Message) -> None:
    """
    Sends the question to the backend to be answered.

    :param message: The message object received from the user.

    :return: None
    """
    db.add_message(
        message.id,
        message.chat.id,
        message.text,
        (message.reply_to_message.id if message.reply_to_message is not None else None),
    )

    if db.get_user_role(message.chat.id) == "unauthorized":
        if re.fullmatch(r"/^\S+@\S+\.\S+$/", message.text):
            check_email(message)
        else:
            bot.reply_to(
                message=message,
                text="Unauthorized user, please send me your email.",
            )
            db.authorize_user(message.chat.id, "test@example.com")

        return

    question = message.text

    logging.info(
        f"User @{message.from_user.username} with chat id {message.chat.id} sent a question: {question}"
    )

    bot.reply_to(
        message=message,
        text=format_for_telegram(
            c.question(question, db.get_last_n_messages(message.chat.id, 3))
        ),
    )


def start_bot() -> None:
    """
    Starts the bot.

    :return: None
    """
    bot.infinity_polling()
