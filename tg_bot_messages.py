def get_start_text(user_name: str) -> str:
    return f"""
Hi, {user_name}! 
Welcome to the 'Life Aquatic' exotic aquarium fish store!
"""


def get_user_email_text(user_name: str) -> str:
    return f"""
Dear {user_name},
please leave your email to get a call from our manager.
"""


def get_customer_creation_text(customer_id: str, customer_email: str):
    return f"""
Your order ID is {customer_id}.
Thank you for placing an order in 'Life Aquatic' store.
Our manager will get in touch with you soon on {customer_email}.
"""


def get_product_description_text(product: dict) -> str:
    product_details = product["data"]
    return f"""
Name: {product_details['name']}
------
Price: {product_details['meta']['display_price']['with_tax']['formatted']} per unit
Stock: {product_details['meta']['stock']['level']} units available
------
Description: {product_details['description']}
"""


def get_product_summary_text(
    name: str, price: int, quantity: int, description: str
) -> str:
    formatted_price = "{:.2f}".format(price)
    formatted_subtotal = "{:.2f}".format(price * quantity)
    return f"""
Name: {name}
------
Price: ${formatted_price} per unit
Quantity: {quantity} units
Subtotal: ${formatted_subtotal}
------
Description: {description}
------------------------
"""


def get_cart_summary_text(cart_items: dict) -> str:
    total_price = 0
    products = []

    for product in cart_items:
        name = product["name"]
        price = (product["value"]["amount"]) / 100
        quantity = product["quantity"]
        description = product["description"]

        total_price += price * quantity

        product_summary: str = get_product_summary_text(
            name, price, quantity, description
        )
        products.append(product_summary)

    formatted_total_price = "{:.2f}".format(total_price)
    message_total_price = f"TOTAL: ${formatted_total_price}"

    message_products_lines = "\n".join(products)
    cart_summary = f"{message_total_price}\n{message_products_lines}"

    return cart_summary
