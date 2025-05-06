import logging
from datetime import datetime, timedelta
from django.core.cache import cache
from rest_framework.response import Response
from .enums import ActionTTL, get_ttl_delta
from main.constants import CACHE_DELIMITER


def check_ttl(request, prefix):
    request_timestamp_str = request.data.get('context', {}).get('timestamp')
    if not request_timestamp_str:
        return Response({"error": "Missing request timestamp"}, status=400)
    logging.info(f"Request timestamp=========: {request_timestamp_str}")

    transaction_id = request.data.get('context', {}).get('transaction_id')
    if not transaction_id:
        return Response({"error": "Missing transaction ID"}, status=400)

    start_time_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:{prefix}_start_time"
    logging.info(f"Start time cache key=======: {start_time_cache_key}")
    cached_search_timestamp_str = cache.get(start_time_cache_key)
    if not cached_search_timestamp_str:
        return Response({"error": f"No cached timestamp found for start_time_cache_key: {start_time_cache_key}======= Data: "
                                  f"{cached_search_timestamp_str}"}, status=400)

    logging.info(f"Start time cache key=======: {start_time_cache_key}")

    # Convert string timestamps to datetime objects
    request_timestamp = datetime.strptime(request_timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    cached_search_timestamp = datetime.strptime(cached_search_timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    time_difference = request_timestamp - cached_search_timestamp
    action_name = prefix.upper()
    ttl_enum = get_ttl_delta(action_name=action_name)

    if time_difference > ttl_enum:
        return Response({"ack": {"status": "NACK"}}, status=400)

    return None  # Return None if everything is fine and TTL check passes
