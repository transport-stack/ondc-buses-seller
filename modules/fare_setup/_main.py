import json
import logging
import sqlite3
import time
import psycopg2
from modules.transit_db_connector import get_connection, close_connection, get_cached_connection, connection_cache
from cachetools import TTLCache

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
    stop_name_cache = TTLCache(maxsize=1000, ttl=3600)  # Cache with TTL

    def __init__(self):
        self.conn = self.ensure_connection()
        if self.conn is None:
            logging.error("Failed to establish a database connection")
            raise Exception("Failed to establish a database connection")

    def ensure_connection(self):
        """Ensure the connection is active, otherwise, re-establish it."""
        conn = get_cached_connection()
        try:
            if conn is None or conn.closed:
                conn = get_connection()
            else:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            conn = get_connection()
        if conn:
            connection_cache['db_connection'] = conn
        return conn

    def execute_query(self, query, params):
        self.conn = self.ensure_connection()
        cursor = self.conn.cursor()
        try:
            start_time = time.time()
            cursor.execute(query, params)
            result = cursor.fetchall()
            end_time = time.time()
            logging.info(f"Query executed in {end_time - start_time} seconds")
            return result
        finally:
            cursor.close()
            close_connection(self.conn)

    # def get_fare_given_route_id__start_stop_code__end_stop_code(self, route_id, start_stop_index, end_stop_index, is_ac):
    #     query = f"""
    #         SELECT
    #             (fare_matrix::jsonb #>> '{{{start_stop_index},{end_stop_index}}}') as fare_details,
    #             (stop_details::jsonb #>> '{{{start_stop_index},2}}') as start_latitude,
    #             (stop_details::jsonb #>> '{{{start_stop_index},3}}') as start_longitude,
    #             (stop_details::jsonb #>> '{{{end_stop_index},2}}') as end_latitude,
    #             (stop_details::jsonb #>> '{{{end_stop_index},3}}') as end_longitude
    #         FROM
    #             routes
    #         WHERE
    #             route_id = %s AND is_ac = %s;
    #     """
    #     result = self.execute_query(query, (route_id, is_ac))
    #     if result and result[0] is not None:
    #         fare_json_string = result[0][0]
    #         start_latitude = result[0][1]
    #         start_longitude = result[0][2]
    #         end_latitude = result[0][3]
    #         end_longitude = result[0][4]
    #
    #         if fare_json_string is not None:
    #             try:
    #                 fare_details = json.loads(fare_json_string)
    #                 start_gps = (start_latitude, start_longitude)
    #                 end_gps = (end_latitude, end_longitude)
    #                 data = {
    #                     'fare_details': fare_details,
    #                     'start_gps': start_gps,
    #                     'end_gps': end_gps
    #                 }
    #                 return data
    #             except json.JSONDecodeError:
    #                 logging.error("Failed to decode JSON from fare details.")
    #                 return None
    #         else:
    #             logging.info("No fare details found.")
    #             return None
    #     else:
    #         logging.info("No result fetched from database.")
    #         return None
    #
    # def get_routes_given_start_stop_code__end_stop_code(self, start_stop_code, end_stop_code, is_ac=None):
    #     query = '''
    #         SELECT
    #             a.route_id,
    #             a.name AS start_stop_name,
    #             b.name AS end_stop_name,
    #             a.sequence_in_route AS start_sequence,
    #             b.sequence_in_route AS end_sequence
    #         FROM
    #             stops a
    #         JOIN
    #             stops b ON a.route_id::text = b.route_id::text
    #         JOIN
    #             routes r ON a.route_id::text = r.route_id::text
    #         WHERE
    #             a.code = %s AND b.code = %s AND a.sequence_in_route < b.sequence_in_route AND r.is_active = True
    #     '''
    #     params = [start_stop_code, end_stop_code]
    #     if is_ac is not None:
    #         query += ' AND r.is_ac = %s '
    #         params.append(is_ac)
    #     query += ' ORDER BY a.route_id, a.sequence_in_route, b.sequence_in_route;'
    #
    #     stops_info = self.execute_query(query, tuple(params))
    #     if not stops_info:
    #         raise Exception("No route information found for the specified stops.")
    #
    #     routes_data = [(info[0], info[3], info[4]) for info in stops_info]
    #     logging.info(f"Routes Data: {routes_data}")
    #     return routes_data
    #
    # def get_route_details_given_route_id(self, route_id, is_ac=None):
    #     logging.info(f"Route ID: {route_id}, is_ac: {is_ac}")
    #     query = f"SELECT route_id, name, agency, is_ac FROM routes WHERE route_id IN ({', '.join(['%s'] * len(route_id))}) AND is_active = True"
    #     params = list(route_id)
    #     if is_ac is not None:
    #         query += " AND is_ac = %s"
    #         params.append(is_ac)
    #
    #     route_details = self.execute_query(query, tuple(params))
    #     logging.info(f"Route details: {route_details}")
    #     if not route_details:
    #         raise Exception("No route information found for the specified route_id(s).")
    #
    #     return route_details
    #
    def get_fare_for_route(self, start_stop_code, end_stop_code, route_id, is_ac):
        is_ac = True if is_ac == "AC" else False
        query = """
            SELECT
                routes.fare_matrix::jsonb #>> array[stops.start_sequence::text, stops.end_sequence::text] AS fare_details
            FROM
                (SELECT
                    a.route_id,
                    a.sequence_in_route AS start_sequence,
                    b.sequence_in_route AS end_sequence
                FROM
                    stops a
                JOIN
                    stops b ON a.route_id = b.route_id
                WHERE
                    a.code = %s AND
                    b.code = %s AND
                    a.sequence_in_route < b.sequence_in_route AND
                    a.route_id = %s
                ) AS stops
            JOIN
                routes ON stops.route_id::text = routes.route_id::text AND routes.is_ac = %s AND routes.is_active = TRUE
            ORDER BY
                stops.route_id, stops.start_sequence, stops.end_sequence;
        """
        fare_details_list = self.execute_query(query, (start_stop_code, end_stop_code, route_id, is_ac))
        if fare_details_list:
            fare_details_json = fare_details_list[0][0]
            if fare_details_json:
                fare_details = json.loads(fare_details_json)
                return fare_details
            else:
                return {"bf": None, "tl": None}
        else:
            return {"bf": None, "tl": None}

    def get_combined_route_and_fare_details(self, start_stop_code, end_stop_code, is_ac=None):
        query = """
        WITH route_info AS (
            SELECT DISTINCT
                a.route_id::text as route_id,
                a.name AS start_stop_name,
                b.name AS end_stop_name,
                a.sequence_in_route AS start_sequence,
                b.sequence_in_route AS end_sequence
            FROM
                stops a
            JOIN
                stops b ON a.route_id::text = b.route_id::text
            JOIN
                routes r ON a.route_id::text = r.route_id::text
            WHERE
                a.code = %s
                AND b.code = %s
                AND a.sequence_in_route < b.sequence_in_route
                AND r.is_active = True
        ),
        route_details AS (
            SELECT 
                routes.route_id::text as route_id,
                routes.name, 
                routes.agency, 
                routes.is_ac,
                routes.fare_matrix,
                routes.stop_details
            FROM 
                routes
            WHERE 
                routes.route_id::text IN (SELECT route_info.route_id FROM route_info)
        """

        # Add is_ac filter if provided
        params = [start_stop_code, end_stop_code]
        if is_ac is not None:
            query += " AND routes.is_ac = %s"
            params.append(is_ac)

        query += """
        )
        SELECT DISTINCT
            ri.route_id,
            rd.name,
            rd.agency,
            rd.is_ac,
            ri.start_sequence,
            ri.end_sequence,
            (rd.fare_matrix::jsonb #>> array[ri.start_sequence::text, ri.end_sequence::text]) as fare_details,
            (rd.stop_details::jsonb #>> array[ri.start_sequence::text, '2']) as start_latitude,
            (rd.stop_details::jsonb #>> array[ri.start_sequence::text, '3']) as start_longitude,
            (rd.stop_details::jsonb #>> array[ri.end_sequence::text, '2']) as end_latitude,
            (rd.stop_details::jsonb #>> array[ri.end_sequence::text, '3']) as end_longitude,
            ri.start_stop_name,
            ri.end_stop_name
        FROM
            route_info ri
        JOIN
            route_details rd ON ri.route_id = rd.route_id
        JOIN
            routes r ON ri.route_id = r.route_id::text
        WHERE
            r.is_active = True
        """

        # Add is_ac filter to the main query if provided
        if is_ac is not None:
            query += " AND rd.is_ac = %s"
            params.append(is_ac)

        query += ";"

        results = self.execute_query(query, tuple(params))

        if not results:
            logging.info("No result fetched from database.")
            return None

        combined_details = []
        for result in results:
            fare_json_string = result[6]
            if fare_json_string is not None:
                try:
                    fare_details = json.loads(fare_json_string)
                    start_gps = (result[7], result[8])
                    end_gps = (result[9], result[10])
                    data = {
                        'route_id': result[0],
                        'route_name': result[1],
                        'num_of_stops': 0,
                        'air_conditioned': result[3],
                        'agency': result[2],
                        'fare': fare_details.get('bf', None),
                        'direction': f"{result[11]} to {result[12]}",
                        'start_stop_gps': start_gps,
                        'end_stop_gps': end_gps,
                        'start_stop_name': result[11],
                        'end_stop_name': result[12]
                    }
                    combined_details.append(data)
                except json.JSONDecodeError:
                    logging.error("Failed to decode JSON from fare details.")
                    continue
            else:
                logging.info("No fare details found.")
                continue

        return combined_details

    # def get_stop_name_from_code(self, stop_code):
    #     if stop_code in FareCalculator.stop_name_cache:
    #         logging.info(f"Cache hit for stop code: {stop_code}")
    #         return FareCalculator.stop_name_cache[stop_code]
    #
    #     query = '''
    #         SELECT name
    #         FROM stops
    #         WHERE code = %s
    #     '''
    #     stop_name = self.execute_query(query, (stop_code,))
    #     if stop_name:
    #         FareCalculator.stop_name_cache[stop_code] = stop_name[0][0]
    #         return stop_name[0][0]
    #     else:
    #         return None

    def fetch_intermediate_stops_with_gps(self, start_stop_code, end_stop_code):
        # Query to get the common route ID
        common_route_query = """
            SELECT route_id 
            FROM stops 
            WHERE code = %s
            INTERSECT 
            SELECT route_id 
            FROM stops 
            WHERE code = %s
        """
        route_id_result = self.execute_query(common_route_query, (start_stop_code, end_stop_code))
        if not route_id_result:
            return "No common route found."

        # TODO: Check if all routes are being processed
        route_id = route_id_result[0][0]

        # Query to get intermediate stops and their details
        intermediate_stops_query = """
            SELECT 
                s.name, 
                s.code,
                s.sequence_in_route,
                r.stop_details
            FROM 
                stops s
            JOIN 
                routes r ON s.route_id::text = r.route_id::text
            WHERE 
                s.route_id = %s AND
                s.sequence_in_route > (
                    SELECT sequence_in_route 
                    FROM stops 
                    WHERE code = %s AND route_id = s.route_id LIMIT 1
                ) AND
                s.sequence_in_route < (
                    SELECT sequence_in_route 
                    FROM stops 
                    WHERE code = %s AND route_id = s.route_id LIMIT 1
                )
            ORDER BY 
                s.sequence_in_route
        """
        intermediate_stops = self.execute_query(intermediate_stops_query, (route_id, start_stop_code, end_stop_code))

        if not intermediate_stops:
            return "No intermediate stops found."

        stop_details = json.loads(intermediate_stops[0][3])
        result = []

        for index, (name, code, sequence, _) in enumerate(intermediate_stops):
            stop_info = stop_details[sequence]
            latitude, longitude = stop_info[2], stop_info[3]
            formatted_latitude = f"{latitude:.6f}"
            formatted_longitude = f"{longitude:.6f}"
            result.append({
                "type": "INTERMEDIATE_STOP",
                "instructions": {"name": f"Stop {index + 1}"},
                "location": {
                    "descriptor": {"name": name, "code": code},
                    "gps": f"{formatted_latitude}, {formatted_longitude}"
                },
                "id": f"{index + 2}",
                "parent_stop_id": f"{index + 1}"
            })

        return result

    def close(self):
        close_connection(self.conn)
