from elastic import get_all_products
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_menu_markup(elastic_token: str):
    products = get_all_products(credential_token=elastic_token)["data"]
    product_names_and_ids = [(product["name"], product["id"]) for product in products]

    keyboard = [
        [
            InlineKeyboardButton(text=product_name, callback_data=product_id)
            for product_name, product_id in product_names_and_ids
        ],
        [InlineKeyboardButton("Cart", callback_data="cart")],
    ]
    menu_markup = InlineKeyboardMarkup(keyboard)

    return menu_markup


def get_description_markup():
    keyboard = [
        [
            InlineKeyboardButton("1 unit", callback_data=1),
            InlineKeyboardButton("5 units", callback_data=5),
            InlineKeyboardButton("10 units", callback_data=10),
        ],
        [InlineKeyboardButton(text="Back to menu", callback_data="back")],
        [InlineKeyboardButton("Cart", callback_data="cart")],
    ]
    description_markup = InlineKeyboardMarkup(keyboard)

    return description_markup
