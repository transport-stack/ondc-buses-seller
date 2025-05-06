import datetime
import json
import logging
import sqlite3
import time
import psycopg2
from django.db import connections
# from modules.transit_db_connector import get_connection, close_connection, get_cached_connection, connection_cache
from cachetools import TTLCache
from django.db.utils import OperationalError

static_bus_dict = {
    "Delhi Transport Corporation": {
        "AC": {
            "bus_reg_num": "DL1PC9997",
        },
        "NAC": {
            "bus_reg_num": "DL1PC7021",
        }
    },
    "Delhi Integrated Multi-Modal Transit System": {
        "AC": {
            "bus_reg_num": "DL1PD5275",
        },
        "NAC": {
            "bus_reg_num": "DL1PD5228",
        }
    }
}

static_bus_dict_short_code = {
    "DTC": {
        "AC": {
            "bus_reg_num": "DL1PC9997",
        },
        "NAC": {
            "bus_reg_num": "DL1PC7021",
        }
    },
    "DIMTS": {
        "AC": {
            "bus_reg_num": "DL1PD5275",
        },
        "NAC": {
            "bus_reg_num": "DL1PD5228",
        }
    }
}


class FareCalculator:
    stop_name_cache = TTLCache(maxsize=1000, ttl=3600)

    def execute_query(self, query, params=None, header=False):
        """Execute a query and return results."""
        try:
            # Get the connection directly from Django's connection management
            conn = connections['transit_db']

            # Use the connection's cursor to execute the query
            with conn.cursor() as cursor:
                start_time = time.time()

                # Execute the query with or without parameters
                if params is None:
                    cursor.execute(query)
                else:
                    cursor.execute(query, params)

                result = cursor.fetchall()
                headers = cursor.description
                end_time = time.time()
                logging.info(f"Query executed in {end_time - start_time} seconds")

                # Return result with or without headers based on the input flag
                if header:
                    return result, headers
                else:
                    return result
        except OperationalError as e:
            logging.error(f"Database connection error: {e}")
            return None
        except Exception as e:
            logging.error(f"Error executing query: {e}")
            return None

    def get_fare_for_route(self, start_stop_code, end_stop_code, route_id, is_ac):
        _is_ac = True if is_ac == "AC" else False
        query = "select fare_details from stops_pair_new where start_stop_code = %s and end_stop_code = %s and route_id = %s and is_ac = %s;"

        fare_details_list = self.execute_query(query, (start_stop_code, end_stop_code, route_id, _is_ac))
        if fare_details_list and fare_details_list[0][0]:
            fare_details_json = fare_details_list[0][0]
            return json.loads(fare_details_json)
        else:
            return {"bf": None, "tl": None}

    def get_combined_route_and_fare_details(self, start_stop_code, end_stop_code, is_ac=None):
        start = datetime.datetime.now()

        if is_ac is not None:
            query = "select * from stops_pair_new where start_stop_code = %s and end_stop_code = %s and is_ac = %s;"
            params = [start_stop_code, end_stop_code, is_ac]
        else:
            print("is_ac is None")
            query = "select * from stops_pair_new where start_stop_code = %s and end_stop_code = %s;"
            params = [start_stop_code, end_stop_code]

        results, headers = self.execute_query(query, tuple(params), True)

        route_details = [dict(zip([x[0] for x in headers], row)) for row in results]
        sequence_dict = {x['route_id']: [x['start_sequence'], x['end_sequence']] for x in route_details}
        if not results:
            logging.info("No result fetched from database.")
            return None

        combined_details = []
        for result in route_details:
            fare_json_string = result['fare_details']
            if fare_json_string is not None:
                try:
                    fare_details = json.loads(fare_json_string)
                    # start_gps = (result[7], result[8])
                    # end_gps = (result[9], result[10])
                    data = {
                        'route_id': result['route_id'],
                        'route_name': result['name'],
                        'num_of_stops': 0,
                        'air_conditioned': result['is_ac'],
                        'agency': result['agency'],
                        'fare': fare_details.get('bf', None),
                        'direction': f"{start_stop_code} to {end_stop_code}",
                        # 'direction': f"{result[11]} to {result[12]}",
                        'start_stop_gps': "0.000000",
                        'end_stop_gps': "0.000000",
                        'start_stop_name': result['start_stop_name'],
                        'end_stop_name': result['end_stop_name'],
                        # 'start_stop_name': result[11],
                        # 'end_stop_name': result[12]
                    }
                    combined_details.append(data)
                except json.JSONDecodeError:
                    logging.error("Failed to decode JSON from fare details.")
                    continue
            else:
                logging.info("No fare details found.")
                continue

        print(f'Time taken : {datetime.datetime.now() -  start}')
        return combined_details, sequence_dict

    # def fetch_intermediate_stops_with_gps(self, start_stop_code, end_stop_code):
    def fetch_intermediate_stops_with_gps(self, routes, start_stop_code, end_stop_code, sequence_dict):
        query = f"select * from stops_new where route_id::int in ({routes});"
        route_id_result, headers = self.execute_query(query, None, True)
        route_details = [dict(zip([x[0] for x in headers], row)) for row in route_id_result]

        if not route_details:
            return "No common route found."

        def get_stops_in_route(route_details):
            segments = {}
            for stop in route_details:
                if stop['route_id'] not in segments:
                    segments[stop['route_id']] = []
                segments[stop['route_id']].append(stop)

            return segments

        def get_route_segment(route_details, start_index, end_index):
            if start_index < end_index:
                segment = route_details[start_index + 1:end_index]
            else:
                segment = []
                logging.fatal("Start stop comes after end stop in the route sequence")

            return segment

        stops_in_route = get_stops_in_route(route_details)

        result = {}
        for route, stops in stops_in_route.items():
            start_index = sequence_dict[int(route)][0]
            end_index = sequence_dict[int(route)][1]

            # Skip processing if indices are invalid
            if start_index >= len(stops) or end_index > len(stops) or start_index >= end_index:
                logging.warning(f"Invalid indices for route {route}: start_index={start_index}, end_index={end_index}")
                result[route] = []
                continue

            intermediate_stops = get_route_segment(stops, start_index, end_index)
            if len(intermediate_stops) == 0:
                result[route] = intermediate_stops
                continue
            for idx, stop in enumerate(intermediate_stops, 1):
                latitude, longitude = 0.0, 0.0
                formatted_latitude = f"{latitude:.6f}"
                formatted_longitude = f"{longitude:.6f}"
                if stop['route_id'] not in result:
                    result[stop['route_id']] = []
                result[stop['route_id']].append({
                    "type": "INTERMEDIATE_STOP",
                    "instructions": {"name": f"Stop {idx}"},
                    "location": {
                        "descriptor": {"name": stop['name'], "code": stop['code']},
                        "gps": f"{formatted_latitude}, {formatted_longitude}"
                    },
                    "id": f"{idx + 1}",
                    "parent_stop_id": f"{idx}"
                })

        return result

    # def close_all_connection(self):
    #     if self.conn:
    #         close_connection(self.conn)  # Use your close_connection utility
    #         logging.info("Connection closed and removed from cache")
