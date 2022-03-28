# Fish Store Telegram Bot

This project is a simple telegram store bot for your Fish Store.
Powered by [Elasticpath Commerce Cloud CMS][https://www.elasticpath.com/elastic-path-commerce-cloud]

## Examples
Try this telegram bot: `@dvmn_fish_store_bot`

## Features
- `long polling` Telegram API utilization
- `Elasticpath` (Moltin) CMS integration
- Create customer in `Elasticpath`
- Get all available `Elasticpath` products
- Get detailed `Elasticpath` product description
- Add or delete products from `Elasticpath` cart
- Get total price and products in `Elasticpath` cart
- Get user email for future billing operations

## Installation
1. Clone project
```bash
git clone https://github.com/gennadis/fish-store.git
cd fish-store
```

2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install requirements
```bash
pip install -r requirements.txt
```

4. Rename `.env.example` to `.env` and fill your secrets in it.  
```bash
ELASTICPATH_CLIENT_ID=your_elasticpath_client_id
ELASTICPATH_CLIENT_SECRET=your_elasticpath_client_secret

TELEGRAM_TOKEN=your_telegram_bot_token

REDIS_ADDRESS=redis_cloud_db_uri:PORT
REDIS_PASSWORD=your_redis_db_password
REDIS_NAME=0
```

5. Run bot
```bash
python tg_bot.py
```
