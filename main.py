import os
from pprint import pprint

import requests
from dotenv import load_dotenv


def get_credential_token(client_id: str, client_secret: str) -> str:
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    response = requests.post("https://api.moltin.com/oauth/access_token", data=data)
    response.raise_for_status()

    return response.json()["access_token"]


def get_pcm_catalog_releases(credential_token: str, catalog_id: str) -> dict:
    headers = {"Authorization": f"Bearer {credential_token}"}
    response = requests.get(
        f"https://api.moltin.com/pcm/catalogs/{catalog_id}/releases", headers=headers
    )
    response.raise_for_status()

    return response.json()


def delete_pcm_catalog_releases(credential_token: str, catalog_id: str) -> int:
    headers = {"Authorization": f"Bearer {credential_token}"}
    response = requests.delete(
        f"https://api.moltin.com/pcm/catalogs/{catalog_id}/releases", headers=headers
    )
    response.raise_for_status()

    return response.status_code


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


def main():
    load_dotenv()
    client_id = os.getenv("ELASTICPATH_CLIENT_ID")
    client_secret = os.getenv("ELASTICPATH_CLIENT_SECRET")
    catalog_id = os.getenv("CATALOG_ID")

    credential_token = get_credential_token(client_id, client_secret)

    products = get_all_products(credential_token)
    products_ids = [product["id"] for product in products["data"]]

    # product_adding_status = add_product_to_cart(
    #     credential_token=credential_token,
    #     product_id=products_ids[1],
    #     quantity=1,
    #     cart_id="abc",
    # )
    # pprint(product_adding_status)

    cart = get_cart(credential_token=credential_token, cart_id="abc")
    pprint(cart)


if __name__ == "__main__":
    main()
