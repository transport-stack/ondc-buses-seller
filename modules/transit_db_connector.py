# import logging
# import os
# import psycopg2
# from psycopg2 import pool
# import time
# from cachetools import TTLCache
#
# # Initialize the connection pool with a higher maximum number of connections
# db_pool = psycopg2.pool.SimpleConnectionPool(
#     1, 2,  # Initial minimum and maximum connections
#     dbname=os.environ.get('TRANSIT_DB_NAME'),
#     user=os.environ.get('TRANSIT_DB_USER'),
#     password=os.environ.get('TRANSIT_DB_PASS'),
#     host=os.environ.get('TRANSIT_DB_HOST'),
#     port='5432'
# )
#
# # Connection cache with TTL
# connection_cache = TTLCache(maxsize=50, ttl=60)  # Cache size and TTL in seconds
#
#
# def get_cached_connection():
#     cache_key = 'db_connection'
#     if cache_key in connection_cache:
#         connection = connection_cache[cache_key]
#         if validate_connection(connection):  # Validate the connection before reuse
#             return connection
#         else:
#             del connection_cache[cache_key]  # Invalidate the cache if connection is not valid
#
#     connection = get_connection()
#     if connection:
#         connection_cache[cache_key] = connection
#     return connection
#
#
# def validate_connection(connection):
#     try:
#         with connection.cursor() as cur:
#             cur.execute("SELECT 1")
#         return True
#     except psycopg2.Error:
#         return False
#
#
# def get_connection(retries=5, delay=1, backoff=2):
#     for i in range(retries):
#         try:
#             connection = db_pool.getconn()
#             if connection:
#                 logging.info("Successfully got a connection from the pool")
#                 return connection
#         except psycopg2.Error as error:
#             logging.error(f"Error while getting connection from pool: {error}")
#             time.sleep(delay)
#             delay *= backoff  # Exponential backoff
#     logging.error("Failed to get connection after retries")
#     return None
#
#
# def close_connection(connection):
#     if connection is not None:
#         db_pool.putconn(connection)
#         cache_key = 'db_connection'
#         if cache_key in connection_cache:
#             del connection_cache[cache_key]
#         logging.info("Connection returned to pool and removed from cache")
