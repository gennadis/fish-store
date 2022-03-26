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

    return response.json()["data"]


def main():
    load_dotenv()
    client_id = os.getenv("ELASTICPATH_CLIENT_ID")
    client_secret = os.getenv("ELASTICPATH_CLIENT_SECRET")
    catalog_id = os.getenv("CATALOG_ID")

    credential_token = get_credential_token(client_id, client_secret)

    products = get_all_products(credential_token)
    pprint(products)


if __name__ == "__main__":
    main()
