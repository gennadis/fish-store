import logging
import os
import time
from enum import Enum, auto
from textwrap import dedent


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


logger = logging.getLogger(__file__)


class State(Enum):
    HANDLE_MENU = auto()
    HANDLE_DESCRIPTION = auto()
    HANDLE_CART = auto()
    WAITING_EMAIL = auto()


def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Telegram bot encountered an error", exc_info=context.error)


def validate_token_expiration(function_to_decorate):
    def wrapper(*args, **kwagrs):
        update, context = args
        token_expiration_time = context.bot_data.get("token_expires")
        current_time = time.time()

        if current_time >= token_expiration_time:
            logger.info("Getting new Elastic token due to expiration.")

            client_id = context.bot_data["elastic_client_id"]
            client_secret = context.bot_data["elastic_client_secret"]
            new_elastic_token = elastic.get_credential_token(client_id, client_secret)

            context.bot_data["elastic"] = new_elastic_token["access_token"]
            context.bot_data["token_expires"] = new_elastic_token["expires"]

            updated_args = update, context
            return function_to_decorate(*updated_args, **kwagrs)

        return function_to_decorate(*args, **kwagrs)

    return wrapper


@validate_token_expiration
def handle_menu(update: Update, context: CallbackContext) -> State:
    user_first_name = update.effective_user.first_name
    elastic_token = context.bot_data.get("elastic")
    products_markup = keyboards.get_menu_markup(elastic_token)

    update.effective_message.reply_text(
        text=dedent(
            f"""
            Hi, {user_first_name}! 
            Welcome to the 'Life Aquatic' exotic aquarium fish store!
            """
        ),
        reply_markup=products_markup,
    )

    return State.HANDLE_DESCRIPTION


@validate_token_expiration
def handle_description(update: Update, context: CallbackContext) -> State:
    query = update.callback_query
    query.answer()

    elastic_token = context.bot_data.get("elastic")
    product = elastic.get_product(credential_token=elastic_token, product_id=query.data)

    product_details = product["data"]
    product_description = f"""
        Name: {product_details['name']}
        ------
        Price: {product_details['meta']['display_price']['with_tax']['formatted']} per unit
        Stock: {product_details['meta']['stock']['level']} units available
        ------
        Description: {product_details['description']}"""
    formatted_product_description = "\n".join(
        line.strip() for line in product_description.splitlines()
    )

    context.bot_data["product_id"] = product["data"]["id"]

    picture_id = product["data"]["relationships"]["main_image"]["data"]["id"]
    picture_href = elastic.get_file_href(
        credential_token=elastic_token, file_id=picture_id
    )

    update.effective_user.send_photo(
        photo=picture_href,
        caption=formatted_product_description,
        reply_markup=keyboards.get_description_markup(),
    )
    update.effective_message.delete()

    return State.HANDLE_DESCRIPTION


@validate_token_expiration
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


@validate_token_expiration
def handle_cart(update: Update, context: CallbackContext) -> State:
    query = update.callback_query
    query.answer()

    elastic_token = context.bot_data.get("elastic")
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

    update.effective_user.send_message(
        text=elastic.get_cart_summary_text(cart_items=cart_items["data"]),
        reply_markup=keyboards.get_cart_markup(cart_items=cart_items),
    )
    update.effective_message.delete()

    return State.HANDLE_CART


@validate_token_expiration
def handle_user_email(update: Update, context: CallbackContext) -> State:
    user_first_name = update.effective_user.first_name
    query = update.callback_query
    query.answer()

    update.effective_user.send_message(
        text=dedent(
            f"""
            Dear {user_first_name},
            please leave your email to get a call from our manager.
            """
        ),
        reply_markup=keyboards.get_email_markup(),
    )

    return State.WAITING_EMAIL


@validate_token_expiration
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
        text=dedent(
            f"""
            Your order ID is {customer["id"].split("-")[0]}.
            Thank you for placing order in 'Life Aquatic' store.
            Our manager will get in touch with you soon on {customer["email"]}.
            """
        ),
        reply_markup=keyboards.get_email_markup(),
    )

    return State.HANDLE_MENU


def run_bot(
    telegram_token: str,
    redis_connection: redis.Redis,
    elastic_token: str,
    elastic_client_id: str,
    elastic_client_secret: str,
):
    updater = Updater(token=telegram_token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.bot_data["redis"] = redis_connection
    dispatcher.bot_data["elastic"] = elastic_token["access_token"]
    dispatcher.bot_data["token_expires"] = elastic_token["expires"]
    dispatcher.bot_data["elastic_client_id"] = elastic_client_id
    dispatcher.bot_data["elastic_client_secret"] = elastic_client_secret

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

    elastic_client_id = os.getenv("ELASTICPATH_CLIENT_ID")
    elastic_client_secret = os.getenv("ELASTICPATH_CLIENT_SECRET")
    elastic_token = elastic.get_credential_token(
        client_id=elastic_client_id, client_secret=elastic_client_secret
    )

    redis_connection = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=os.getenv("REDIS_PORT"),
        db=os.getenv("REDIS_NAME"),
        password=os.getenv("REDIS_PASSWORD"),
    )

    run_bot(
        telegram_token=telegram_token,
        redis_connection=redis_connection,
        elastic_token=elastic_token,
        elastic_client_id=elastic_client_id,
        elastic_client_secret=elastic_client_secret,
    )


if __name__ == "__main__":
    main()
