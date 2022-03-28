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
    name: str, price: str, quantity: str, description: str
) -> str:
    return f"""
Name: {name}
------
Price: {price} per unit
Quantity: {quantity} units
Subtotal: ${float(price.strip('$')) * int(quantity)}
------
Description: {description}
------------------------
"""


def get_cart_summary_text(cart: dict, cart_items: dict) -> str:
    cart_total_price = cart["meta"]["display_price"]["with_tax"]["formatted"]

    products = []
    for product in cart_items:
        product_summary = get_product_summary_text(
            name=product["name"],
            price=product["meta"]["display_price"]["without_tax"]["value"]["formatted"],
            quantity=product["quantity"],
            description=product["description"],
        )

        products.append(product_summary)

    message_first_line = f"TOTAL: {cart_total_price}"
    message_other_lines = "\n".join(products)
    cart_summary = f"{message_first_line}\n{message_other_lines}"

    return cart_summary
