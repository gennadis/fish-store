import os
import logging
import redis

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

from redis_connection import get_redis_connection

logger = logging.getLogger(__file__)


def error_handler(update, context):
    logger.error(msg="Telegram bot encountered an error", exc_info=context.error)


def start(update: Update, context: CallbackContext):
    """
    Хэндлер для состояния START.

    Бот отвечает пользователю фразой "Привет!" и переводит его в состояние ECHO.
    Теперь в ответ на его команды будет запускаеться хэндлер echo.
    """
    user_name = update.effective_user.first_name
    keyboard = [
        [
            InlineKeyboardButton("Option 1", callback_data="1"),
            InlineKeyboardButton("Option 2", callback_data="2"),
        ],
        [InlineKeyboardButton("Option 3", callback_data="3")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        text=f"Привет, {user_name}! Я - бот рыбного магазина", reply_markup=reply_markup
    )

    return "ECHO"


def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    query.edit_message_text(text=f"Selected option: {query.data}")


def echo(update: Update, context: CallbackContext):
    """
    Хэндлер для состояния ECHO.

    Бот отвечает пользователю тем же, что пользователь ему написал.
    Оставляет пользователя в состоянии ECHO.
    """
    users_reply = update.message.text
    update.message.reply_text(users_reply)

    return "ECHO"


def handle_users_reply(update, context):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его написать "/start",
    поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может воспользоваться этой командой.
    """
    redis_connection: redis.Redis = context.bot_data.get("redis")

    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return

    if user_reply == "/start":
        user_state = "START"
        update.message.reply_text(user_state)
    else:
        user_state = redis_connection.get(chat_id).decode("utf-8")
        update.message.reply_text(user_state)

    states_functions = {"START": start, "ECHO": echo}
    state_handler = states_functions[user_state]
    # Если вы вдруг не заметите, что python-telegram-bot перехватывает ошибки.
    # Оставляю этот try...except, чтобы код не падал молча.
    # Этот фрагмент можно переписать.
    try:
        next_state = state_handler(update, context)
        redis_connection.set(chat_id, next_state)
    except Exception as err:
        print(err)


def main():
    logging.basicConfig(level=logging.INFO)

    load_dotenv()
    telegram_token = os.getenv("TELEGRAM_TOKEN")

    redis_address = os.getenv("REDIS_ADDRESS")
    redis_name = os.getenv("REDIS_NAME")
    redis_password = os.getenv("REDIS_PASSWORD")

    redis_connection = get_redis_connection(
        redis_address=redis_address,
        redis_name=redis_name,
        redis_password=redis_password,
    )

    updater = Updater(token=telegram_token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.bot_data["redis"] = redis_connection
    dispatcher.add_error_handler(error_handler)

    dispatcher.add_handler(CallbackQueryHandler(button))
    # dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler("start", handle_users_reply))

    updater.start_polling()
    updater.idle()
    logger.info("Telegram bot started")


if __name__ == "__main__":
    main()