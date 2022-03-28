import requests
from textwrap import dedent


def get_credential_token(client_id: str, client_secret: str) -> str:
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    response = requests.post("https://api.moltin.com/oauth/access_token", data=data)
    response.raise_for_status()

    return response.json()["access_token"]


def get_all_products(credential_token: str) -> dict:
    headers = {"Authorization": f"Bearer {credential_token}"}
    response = requests.get("https://api.moltin.com/v2/products", headers=headers)
    response.raise_for_status()

    return response.json()


def add_product_to_cart(
    credential_token: str, product_id: str, quantity: int, cart_id: str
) -> dict:
    headers = {"Authorization": f"Bearer {credential_token}"}
    json_data = {
        "data": {
            "id": product_id,
            "type": "cart_item",
            "quantity": quantity,
        }
    }
    response = requests.post(
        f"https://api.moltin.com/v2/carts/{cart_id}/items",
        headers=headers,
        json=json_data,
    )
    response.raise_for_status()

    return response.json()


def delete_product_from_cart(
    credential_token: str, cart_id: str, product_id: str
) -> dict:
    headers = {"Authorization": f"Bearer {credential_token}"}
    response = requests.delete(
        f"https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}", headers=headers
    )
    response.raise_for_status()

    return response.json()


def get_cart(credential_token: str, cart_id: str) -> dict:
    headers = {"Authorization": f"Bearer {credential_token}"}
    response = requests.get(
        f"https://api.moltin.com/v2/carts/{cart_id}", headers=headers
    )
    response.raise_for_status()

    return response.json()


def get_cart_items(credential_token: str, cart_id: str) -> dict:
    headers = {"Authorization": f"Bearer {credential_token}"}
    response = requests.get(
        f"https://api.moltin.com/v2/carts/{cart_id}/items", headers=headers
    )
    response.raise_for_status()

    return response.json()


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


def get_product(credential_token: str, product_id: str) -> dict:
    headers = {"Authorization": f"Bearer {credential_token}"}
    response = requests.get(
        f"https://api.moltin.com/v2/products/{product_id}", headers=headers
    )
    response.raise_for_status()

    return response.json()


def get_product_summary_text(
    name: str, price: int, quantity: int, description: str
) -> str:
    formatted_price = "{:.2f}".format(price)
    formatted_subtotal = "{:.2f}".format(price * quantity)
    product_summary_text = dedent(
        f"""\
        Name: {name}
        ------
        Price: ${formatted_price} per unit
        Quantity: {quantity} units
        Subtotal: ${formatted_subtotal}
        ------
        Description: {description}
        ------
        """
    )

    return product_summary_text


def get_file_href(credential_token: str, file_id: str) -> str:
    headers = {"Authorization": f"Bearer {credential_token}"}
    response = requests.get(
        f"https://api.moltin.com/v2/files/{file_id}", headers=headers
    )
    response.raise_for_status()
    file_details = response.json()["data"]

    return file_details["link"]["href"]


def create_customer(credential_token: str, user_id: str, email: str) -> dict:
    headers = {"Authorization": f"Bearer {credential_token}"}
    payload = {
        "data": {
            "type": "customer",
            "name": str(user_id),
            "email": str(email),
            "password": "mysecretpassword",
        },
    }

    response = requests.post(
        "https://api.moltin.com/v2/customers", headers=headers, json=payload
    )
    response.raise_for_status()

    return response.json()


def get_customer(credential_token: str, customer_id: str) -> dict:
    headers = {"Authorization": f"Bearer {credential_token}"}
    response = requests.get(
        f"https://api.moltin.com/v2/customers/{customer_id}", headers=headers
    )
    response.raise_for_status()

    return response.json()
