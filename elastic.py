import requests


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


def get_product(credential_token: str, product_id: str) -> dict:
    headers = {"Authorization": f"Bearer {credential_token}"}
    response = requests.get(
        f"https://api.moltin.com/v2/products/{product_id}", headers=headers
    )
    response.raise_for_status()

    return response.json()


def get_file_href(credential_token: str, file_id: str) -> str:
    headers = {"Authorization": f"Bearer {credential_token}"}
    response = requests.get(
        f"https://api.moltin.com/v2/files/{file_id}", headers=headers
    )
    response.raise_for_status()
    file_details = response.json()["data"]

    return file_details["link"]["href"]
