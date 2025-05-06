import json
import logging

import redis
from django.conf import settings

from main.constants import CACHE_TIMEOUT


class RedisUtil:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    def redis_set_data(self, key, data, ttl=CACHE_TIMEOUT):
        # Check the type of the existing key
        key_type = self.client.type(key)

        # If the key exists and is not a list, delete the key
        if key_type != 'none' and key_type != 'list':
            logging.warning(
                f"Key '{key}' exists with type '{key_type}'. Clearing key to use as list.")
            self.client.delete(key)

        # Convert data to JSON string
        data_json = json.dumps(data)
        # Push the new data onto the list associated with 'key'
        self.client.rpush(key, data_json)
        # Set expiration for the list
        self.client.expire(key, ttl)
        logging.info(f"Data appended to list in redis with key: {key}")

    def redis_get_data(self, key):
        # Fetch all items in the list associated with 'key'
        data_list_json = self.client.lrange(key, 0, -1)
        if data_list_json:
            logging.info(f"Data list fetched from redis with key: {key}")
            # Convert all items back to Python dicts
            return [json.loads(data_json) for data_json in data_list_json]
        return None
