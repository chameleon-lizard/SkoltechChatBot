import logging
import os

import dotenv
import telebot

from main import Chatbot


def format_for_telegram(text: str) -> str:
    return (
        text.replace("_", "\_")
        .replace("*", "\*")
        .replace("[", "\[")
        .replace("]", "\]")
        .replace("(", "\(")
        .replace(")", "\)")
        .replace("~", "\~")
        .replace("`", "\`")
        .replace(">", "\>")
        .replace("#", "\#")
        .replace("+", "\+")
        .replace("-", "\-")
        .replace("=", "\=")
        .replace("|", "\|")
        .replace("{", "\{")
        .replace("}", "\}")
        .replace(".", "\.")
        .replace("!", "\!")
    )


logging.basicConfig(
    format='[%(threadName)s] %(levelname)s: %(message)s"', level=logging.INFO
)

dotenv.load_dotenv("env")

bot = telebot.TeleBot(
    token=f"{os.environ.get('BOT_TOKEN')}",
    parse_mode="MARKDOWN",
    threaded=True,
)


c = Chatbot(
    f"{os.environ.get('CHATBOT_MODEL')}",
    f"{os.environ.get('API_LINK')}",
    f"{os.environ.get('VSEGPT_TOKEN')}",
    ["orientation.md"],
)
c.build_database()


@bot.message_handler(func=lambda message: message.text in ("/start", "/help", "Help"))
def welcome(message: telebot.types.Message) -> None:
    """
    Handle the user's first message to the bot, sending a greeting and instructions on how to use the bot.

    :param message: The message object received from the user.

    :return: None
    """
    # Replying with welcome message
    bot.reply_to(
        message=message,
        text="Hi there! My name is CyberBoris and I am a kinda smart bot, which can answer questions about Skoltech. Just ask and I will try to help!",
    )


@bot.message_handler(content_types=["text"])
def send_question(message: telebot.types.Message) -> None:
    """
    Sends the question to the backend to be answered.

    :param message: The message object received from the user.

    :return: None
    """
    # Registering new user
    question = message.text

    logging.info(
        f"User @{message.from_user.username} with id {message.from_user.id} sent a question: {question}"
    )

    # Replying with added song info
    bot.reply_to(
        message=message,
        text=format_for_telegram(c.question(question)),
    )


def start_bot() -> None:
    """
    Starts the bot.

    :return: None
    """
    bot.infinity_polling()
