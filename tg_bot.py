import logging
import os
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


def run_bot(telegram_token: str, redis_connection: redis.Redis, elastic_token: str):
    updater = Updater(token=telegram_token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.bot_data["redis"] = redis_connection
    dispatcher.bot_data["elastic"] = elastic_token

    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            State.HANDLE_MENU: [
                CallbackQueryHandler(handle_menu),
            ],
        },
        fallbacks=[MessageHandler(Filters.text, error_handler)],
    )
    dispatcher.add_handler(conversation)
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()
    logger.info("Telegram bot started")


def main():
    logging.basicConfig(level=logging.INFO)

    load_dotenv()
    telegram_token = os.getenv("TELEGRAM_TOKEN")

    elastic_client_id = os.getenv("ELASTICPATH_CLIENT_ID")
    elastic_client_secret = os.getenv("ELASTICPATH_CLIENT_SECRET")
    elastic_token = get_credential_token(elastic_client_id, elastic_client_secret)

    redis_address = os.getenv("REDIS_ADDRESS")
    redis_name = os.getenv("REDIS_NAME")
    redis_password = os.getenv("REDIS_PASSWORD")
    redis_connection = get_redis_connection(
        redis_address=redis_address,
        redis_name=redis_name,
        redis_password=redis_password,
    )

    run_bot(
        telegram_token=telegram_token,
        redis_connection=redis_connection,
        elastic_token=elastic_token,
    )


if __name__ == "__main__":
    main()
