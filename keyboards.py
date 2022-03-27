from elastic import get_all_products
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_products_keyboard_markup(elastic_token: str):
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


def get_description_markup():
    keyboard = [[InlineKeyboardButton(text="Back to menu", callback_data="back")]]
    description_markup = InlineKeyboardMarkup(keyboard)

    return description_markup
