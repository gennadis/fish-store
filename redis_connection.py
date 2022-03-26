import redis

REDIS_USERS_HASH_NAME = "fish_store_customers"


def get_redis_connection(
    redis_address: str, redis_name: str, redis_password: str
) -> redis.Redis:
    redis_url, redis_port = redis_address.rsplit(":")
    redis_connection = redis.Redis(
        host=redis_url, port=redis_port, db=redis_name, password=redis_password
    )

    return redis_connection
