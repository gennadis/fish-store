import os

import requests
from dotenv import load_dotenv


def get_credential_token(client_id: str, client_secret: str):
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    response = requests.post("https://api.moltin.com/oauth/access_token", data=data)

    return response.json()["access_token"]


def main():
    load_dotenv()
    client_id = os.getenv("ELASTICPATH_CLIENT_ID")
    client_secret = os.getenv("ELASTICPATH_CLIENT_SECRET")

    credential_token = get_credential_token(client_id, client_secret)
    print(credential_token)


if __name__ == "__main__":
    main()
