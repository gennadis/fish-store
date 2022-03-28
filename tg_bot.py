import logging
import os
from enum import Enum, auto

import redis
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)

import elastic
import keyboards
import tg_bot_messages
from redis_connection import get_redis_connection


logger = logging.getLogger(__file__)


class State(Enum):
    HANDLE_MENU = auto()
    HANDLE_DESCRIPTION = auto()
    HANDLE_CART = auto()
    WAITING_EMAIL = auto()


def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Telegram bot encountered an error", exc_info=context.error)


def handle_menu(update: Update, context: CallbackContext) -> State:
    user_first_name = update.effective_user.first_name
    elastic_token = context.bot_data.get("elastic")
    products_markup = keyboards.get_menu_markup(elastic_token)

    update.effective_message.reply_text(
        text=tg_bot_messages.get_start_text(user_name=user_first_name),
        reply_markup=products_markup,
    )

    return State.HANDLE_DESCRIPTION


def handle_description(update: Update, context: CallbackContext) -> State:
    query = update.callback_query
    query.answer()

    elastic_token = context.bot_data.get("elastic")
    product = elastic.get_product(credential_token=elastic_token, product_id=query.data)
    product_description = tg_bot_messages.get_product_description_text(product=product)

    context.bot_data["product_id"] = product["data"]["id"]

    picture_id = product["data"]["relationships"]["main_image"]["data"]["id"]
    picture_href = elastic.get_file_href(
        credential_token=elastic_token, file_id=picture_id
    )

    update.effective_message.delete()
    update.effective_user.send_photo(
        photo=picture_href,
        caption=product_description,
        reply_markup=keyboards.get_description_markup(),
    )

    return State.HANDLE_DESCRIPTION


def update_cart(update: Update, context: CallbackContext) -> State:
    query = update.callback_query
    query.answer()

    elastic_token = context.bot_data.get("elastic")
    elastic.add_product_to_cart(
        credential_token=elastic_token,
        product_id=context.bot_data["product_id"],
        quantity=int(query.data),
        cart_id=update.effective_user.id,
    )

    return State.HANDLE_DESCRIPTION


def handle_cart(update: Update, context: CallbackContext) -> State:
    query = update.callback_query
    query.answer()

    elastic_token = context.bot_data.get("elastic")

    cart = elastic.get_cart(
        credential_token=elastic_token,
        cart_id=update.effective_user.id,
    )
    cart_items = elastic.get_cart_items(
        credential_token=elastic_token,
        cart_id=update.effective_user.id,
    )

    product_id = query.data
    if product_id in [product["id"] for product in cart_items["data"]]:
        elastic.delete_product_from_cart(
            credential_token=elastic_token,
            cart_id=update.effective_user.id,
            product_id=query.data,
        )

    update.effective_message.delete()
    update.effective_user.send_message(
        text=tg_bot_messages.get_cart_summary_text(
            cart=cart["data"],
            cart_items=cart_items["data"],
        ),
        reply_markup=keyboards.get_cart_markup(cart_items=cart_items),
    )

    return State.HANDLE_CART


def handle_user_email(update: Update, context: CallbackContext) -> State:
    user_first_name = update.effective_user.first_name
    query = update.callback_query
    query.answer()

    update.effective_user.send_message(
        text=tg_bot_messages.get_user_email_text(user_name=user_first_name),
        reply_markup=keyboards.get_email_markup(),
    )

    return State.WAITING_EMAIL


def handle_customer_creation(update: Update, context: CallbackContext) -> State:
    elastic_token = context.bot_data.get("elastic")

    creation_status = elastic.create_customer(
        credential_token=elastic_token,
        user_id=update.effective_user.id,
        email=update.message.text,
    )["data"]

    customer = elastic.get_customer(
        credential_token=elastic_token, customer_id=creation_status["id"]
    )["data"]

    update.effective_user.send_message(
        text=tg_bot_messages.get_customer_creation_text(
            customer_id=customer["id"].split("-")[0],
            customer_email=customer["email"],
        ),
        reply_markup=keyboards.get_email_markup(),
    )

    return State.HANDLE_MENU


def run_bot(telegram_token: str, redis_connection: redis.Redis, elastic_token: str):
    updater = Updater(token=telegram_token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.bot_data["redis"] = redis_connection
    dispatcher.bot_data["elastic"] = elastic_token

    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", handle_menu)],
        states={
            State.HANDLE_MENU: [
                CallbackQueryHandler(handle_menu),
                CallbackQueryHandler(handle_cart, pattern="cart"),
            ],
            State.HANDLE_DESCRIPTION: [
                CallbackQueryHandler(handle_menu, pattern="back"),
                CallbackQueryHandler(handle_cart, pattern="cart"),
                CallbackQueryHandler(update_cart, pattern="^[0-9]+$"),
                CallbackQueryHandler(handle_description),
            ],
            State.HANDLE_CART: [
                CallbackQueryHandler(handle_menu, pattern="back"),
                CallbackQueryHandler(handle_user_email, pattern="checkout"),
                CallbackQueryHandler(handle_cart),
            ],
            State.WAITING_EMAIL: [
                MessageHandler(Filters.text, handle_customer_creation),
                CallbackQueryHandler(handle_cart, pattern="back"),
                CallbackQueryHandler(handle_user_email),
            ],
        },
        fallbacks=[],
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

    elastic_token = elastic.get_credential_token(
        client_id=os.getenv("ELASTICPATH_CLIENT_ID"),
        client_secret=os.getenv("ELASTICPATH_CLIENT_SECRET"),
    )

    redis_connection = get_redis_connection(
        redis_address=os.getenv("REDIS_ADDRESS"),
        redis_name=os.getenv("REDIS_NAME"),
        redis_password=os.getenv("REDIS_PASSWORD"),
    )

    run_bot(
        telegram_token=telegram_token,
        redis_connection=redis_connection,
        elastic_token=elastic_token,
    )


if __name__ == "__main__":
    main()
