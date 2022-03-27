import os
import logging
import redis
from enum import Enum, auto

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
from elastic import get_credential_token, get_all_products, get_product, get_file_href

logger = logging.getLogger(__file__)


class State(Enum):
    START = auto()
    HANDLE_MENU = auto()


def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Telegram bot encountered an error", exc_info=context.error)


def generate_products_keyboard_markup(elastic_token: str):
    products = get_all_products(credential_token=elastic_token)["data"]
    product_names_and_ids = [(product["name"], product["id"]) for product in products]

    keyboard = [
        [
            InlineKeyboardButton(text=product_name, callback_data=product_id)
            for product_name, product_id in product_names_and_ids
        ]
    ]
    products_markup = InlineKeyboardMarkup(keyboard)

    return products_markup


def start(update: Update, context: CallbackContext):
    user_name = update.effective_user.first_name
    elastic_token = context.bot_data.get("elastic")
    products_markup = generate_products_keyboard_markup(elastic_token)

    update.message.reply_text(
        text=f"Привет, {user_name}! Я - бот рыбного магазина",
        reply_markup=products_markup,
    )

    return State.HANDLE_MENU


def handle_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    elastic_token = context.bot_data.get("elastic")
    product = get_product(credential_token=elastic_token, product_id=query.data)
    product_description = product["data"]["description"]

    picture_id = product["data"]["relationships"]["main_image"]["data"]["id"]
    picture_href = get_file_href(credential_token=elastic_token, file_id=picture_id)

    update.effective_message.delete()
    update.effective_user.send_photo(photo=picture_href, caption=product_description)

    return State.START


def handle_users_reply(update: Update, context: CallbackContext):
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
        user_state = State.START
    else:
        user_state = redis_connection.get(chat_id).decode("utf-8")

    states_functions = {
        State.START: start,
        State.HANDLE_MENU: handle_menu,
    }
    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(update, context)
        redis_connection.set(chat_id, next_state)
    except Exception as err:
        print(err)


def main():
    logging.basicConfig(level=logging.INFO)

    load_dotenv()
    telegram_token = os.getenv("TELEGRAM_TOKEN")

    elastic_client_id = os.getenv("ELASTICPATH_CLIENT_ID")
    elastic_client_secret = os.getenv("ELASTICPATH_CLIENT_SECRET")
    elastic_credential_token = get_credential_token(
        elastic_client_id, elastic_client_secret
    )

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
    dispatcher.bot_data["elastic"] = elastic_credential_token

    dispatcher.add_error_handler(error_handler)

    dispatcher.add_handler(CallbackQueryHandler(handle_menu))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler("start", handle_users_reply))

    updater.start_polling()
    updater.idle()
    logger.info("Telegram bot started")


if __name__ == "__main__":
    main()
