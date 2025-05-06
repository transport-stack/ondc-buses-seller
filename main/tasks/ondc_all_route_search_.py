import json
import logging
import os
import psycopg2
import requests
from celery import shared_task
from main.constants import payments_array
from main.utils.on_search1_page1 import on_search_1_page1
from main.utils.post_request import post_request
from main.utils.time_parser import get_current_utc_timestamp
from modules.fare_setup.main import FareCalculator
import uuid
from datetime import datetime
from main.tasks.task_send_no import task_push_txn_logs


# Function to fetch stops with pagination for a specific agency
def fetch_stops_with_pagination_for_agency(limit, offset, agency):
    query = f'''
        SELECT DISTINCT
            s.name AS stop_name, 
            s.code, 
            s.route_id,
            r.agency,
            r.name AS route_name,
            s.latitude,
            s.longitude,
            s.sequence_in_route

        FROM 
            stops_new AS s 
        JOIN 
            routes_new AS r ON s.route_id::text = r.route_id::text
        WHERE 
            r.agency = '{agency}'
        GROUP BY s.sequence_in_route, r.name, s.code, s.name, 
            s.route_id, r.agency, s.latitude, s.longitude
        ORDER BY s.route_id, s.sequence_in_route
        LIMIT {limit} OFFSET {offset};
    '''
    return FareCalculator().execute_query(query)


# Function to fetch the total number of rows for DTC and DIMTS separately and combined
def fetch_total_rows(limit):
    # Fetch total rows for DTC
    query_dtc = '''
        SELECT COUNT(DISTINCT (s.name, s.code, s.route_id, r.agency, r.name, s.latitude, s.longitude, s.sequence_in_route))
        FROM stops_new AS s 
        JOIN routes_new AS r ON s.route_id::text = r.route_id::text
        WHERE r.agency = 'DTC';
    '''
    dtc_rows = FareCalculator().execute_query(query_dtc)[0][0]

    # Fetch total rows for DIMTS
    query_dimts = '''
        SELECT COUNT(DISTINCT (s.name, s.code, s.route_id, r.agency, r.name, s.latitude, s.longitude, s.sequence_in_route))
        FROM stops_new AS s 
        JOIN routes_new AS r ON s.route_id::text = r.route_id::text
        WHERE r.agency = 'DIMTS';
    '''
    dimts_rows = FareCalculator().execute_query(query_dimts)[0][0]

    # Calculate total pages for DTC and DIMTS separately
    dtc_pages = (dtc_rows + limit - 1) // limit  # Round up for DTC
    dimts_pages = (dimts_rows + limit - 1) // limit  # Round up for DIMTS

    # Total pages is the sum of DTC and DIMTS pages
    total_pages = dtc_pages + dimts_pages
    logging.info(f"Total pages for DTC: {dtc_pages}, DIMTS: {dimts_pages}, Total: {total_pages}")
    return dtc_pages, dimts_pages, total_pages


@shared_task(name="main.tasks.on_search_all_route_stops")
def on_search_all_route_stops(context_data, page_number=1, limit=3000, dtc_offset=0, dimts_offset=0,
                              current_agency='DTC', overall_page_number=1, is_first_page=True):
    try:
        bap_uri = context_data['bap_uri']
        bap_id = context_data.get('bap_id')
        transaction_id = context_data.get('transaction_id')
        bpp_id = os.environ.get('BPP_ID')
        bpp_uri = os.environ.get('BPP_URL')
        formatted_current_utc = get_current_utc_timestamp()
        if bap_uri.endswith('/'):
            bap_uri += 'on_search'
        else:
            bap_uri += '/on_search'

        logging.info(f"bap_uri===========: {bap_uri}")

        # Fetch total rows for both agencies
        dtc_total, dimts_total, total_rows = fetch_total_rows(limit)

        if is_first_page:
            # Generate and send the first page payload
            total_page_count = (dtc_total + dimts_total + limit - 1) // limit
            logging.info(f"total page count ========{total_rows}")
            page1_payload = on_search_1_page1(context_data, total_rows)
            status_code, response = post_request(bap_uri, page1_payload)

            logging.info(f"Response from BAP for Page 1: {status_code}, {response}")

            if status_code != 200:
                logging.error("Failed to send the first page payload.")
                return  # Exit if the first page payload fails to send

            # Proceed to subsequent pages
            is_first_page = False

        # Determine the current agency being processed
        if current_agency == 'DTC':
            # Fetch DTC data with pagination
            stops_data = fetch_stops_with_pagination_for_agency(limit, dtc_offset, 'DTC')
            logging.info(f"Number of DTC stops fetched from the database: {len(stops_data)}")
        else:
            # Fetch DIMTS data with pagination
            stops_data = fetch_stops_with_pagination_for_agency(limit, dimts_offset, 'DIMTS')
            logging.info(f"Number of DIMTS stops fetched from the database: {len(stops_data)}")

        # If no more data, switch agency or stop the process
        if not stops_data:
            if current_agency == 'DTC':
                # Finished with DTC, switch to DIMTS
                logging.info("Finished processing DTC, switching to DIMTS.")
                on_search_all_route_stops(context_data, page_number=1, limit=limit, dimts_offset=0, current_agency='DIMTS', overall_page_number=overall_page_number)
            else:
                logging.info("No more data to send for both agencies.")
            return  # No more data for current agency

        # Initialize variables to hold stops details and routes data
        stops_detail = []
        routes_data = {}
        stop_id_mapping = {}
        stop_counter = 1

        # Iterate over the query result to create route and stop data
        for stop_name, code, route_id, agency, route_name, latitude, longitude, sequence_in_route in stops_data:
            # Make sure stop uniqueness includes route_id
            if (stop_name, code, route_id, agency, route_name) not in stop_id_mapping:
                stop_id = f"s{stop_counter}"
                stop_counter += 1
                stop_id_mapping[(stop_name, code, route_id, agency, route_name, latitude, longitude, sequence_in_route)] = stop_id

                # Create a detailed stop object
                stop_detail = {
                    "id": stop_id,
                    "location": {
                        "descriptor": {"name": stop_name, "code": code},
                        "gps": f"{latitude}, {longitude}"
                    }
                }
                stops_detail.append(stop_detail)

            stop_id = stop_id_mapping[(stop_name, code, route_id, agency, route_name, latitude, longitude, sequence_in_route)]

            # Add the route data
            if route_id not in routes_data:
                routes_data[route_id] = {
                    "route_id": route_id,
                    "route_name": route_name,
                    "agency": agency,
                    "stops": []
                }

            # Avoid duplicates in stops list for the route
            if {"id": stop_id} not in routes_data[route_id]["stops"]:
                routes_data[route_id]["stops"].append({"id": stop_id})

        # Adjust the first and last stops as START and END for each route
        for route_info in routes_data.values():
            stops = route_info['stops']

            if stops:
                stops[0]['type'] = 'START'  # First stop is START
                stops[-1]['type'] = 'END'  # Last stop is END
                for i in range(1, len(stops) - 1):
                    stops[i]['type'] = 'INTERMEDIATE_STOP'
                    stops[i]['parent_stop_id'] = stops[i - 1]['id']
                # Assign parent_stop_id to the END stop from the last INTERMEDIATE stop
                if len(stops) > 1:
                    stops[-1]['parent_stop_id'] = stops[-2]['id']

        # Prepare final formatted data
        formatted_data = {
            "context": {
                "location": {
                    "country": {"code": "IND"},
                    "city": {"code": "std:011"}
                },
                "domain": "ONDC:TRV11",
                "action": "on_search",
                "version": "2.0.1",
                "bap_id": bap_id,
                "bap_uri": context_data["bap_uri"],
                "bpp_id": bpp_id,
                "bpp_uri": bpp_uri,
                "transaction_id": transaction_id,
                "message_id": str(uuid.uuid4()),
                "timestamp": formatted_current_utc,
                "ttl": "PT30S"
            },
            "message": {
                "catalog": {
                    "descriptor": {
                        "name": "Transit Solutions",
                        "images": [{"url": "https://transitsolutions.in/logos/logo.ico", "size_type": "xs"}]
                    },
                    "providers": [{
                        "id": "P1",
                        "descriptor": {
                            "name": "Delhi Transport Corporation" if current_agency == "DTC" else "Delhi Integrated Multi-Modal Transit System",
                            "images": [
                                {
                                    "url": "https://dtc.delhi.gov.in/sites/default/files/DTC/logo/dtc_logo_2.png" if current_agency == "DTC"
                                    else "https://www.dimts.in/images/logo.png",
                                    "size_type": "xs"
                                }
                            ]
                        },
                        "items": [
                            {
                                "id": "I1",
                                "descriptor": {
                                    "name": "Single Journey Ticket",
                                    "code": "SJT",
                                    "images": [
                                        {
                                            "url": "https://dtc.delhi.gov.in/sites/default/files/DTC/logo/dtc_logo_2.png",
                                            "size_type": "xs"
                                        }
                                    ]
                                },
                                "time": {
                                    "label": "Validity",
                                    "duration": "PT1D",
                                    "timestamp": formatted_current_utc
                                }
                            },
                            {
                                "id": "I2",
                                "descriptor": {
                                    "name": "Special Fair Single Journey Ticket",
                                    "code": "SFSJT",
                                    "images": [
                                        {
                                            "url": "https://dtc.delhi.gov.in/sites/default/files/DTC/logo/dtc_logo_2.png",
                                            "size_type": "xs"
                                        }
                                    ]
                                }
                            }
                        ],
                        "fulfillments": [],
                        "payments": payments_array
                    }]
                }
            }
        }

        # Add fulfillments based on routes_data
        for route_id, route_info in routes_data.items():
            # Split the route_name into the identifier and direction
            route_identifier = route_info['route_name'].replace("UP", "").replace("DOWN", "").strip()
            route_direction = "UP" if "UP" in route_info['route_name'] else "DOWN"

            formatted_data["message"]["catalog"]["providers"][0]["fulfillments"].append({
                "id": route_id,  # Use the actual route_id as the fulfillment ID
                "type": "ROUTE",
                "stops": route_info['stops'],
                "vehicle": {"category": "BUS"},
                "tags": [{
                    "descriptor": {"code": "ROUTE_INFO"},
                    "list": [
                        {"descriptor": {"code": "ROUTE_ID"}, "value": route_identifier},  # Route name without UP/DOWN
                        {"descriptor": {"code": "ROUTE_DIRECTION"}, "value": route_direction}  # UP or DOWN
                    ]
                }]
            })

        # Add the stops as a fulfillment with ID 'S1'
        formatted_data["message"]["catalog"]["providers"][0]["fulfillments"].append({
            "id": "S1",
            "type": "STOPS",
            "stops": [{"id": stop['id'], "location": stop["location"]} for stop in stops_detail]
        })

        # Add the pagination tags with dynamic pagination ID
        total_pages = total_rows  # Calculate the total number of pages
        formatted_data["message"]["catalog"]["tags"] = [
            {
                "descriptor": {
                    "code": "PAGINATION",
                    "name": "Pagination"
                },
                "display": True,
                "list": [
                    {
                        "descriptor": {
                            "code": "PAGINATION_ID"
                        },
                        "value": f"P{overall_page_number}"
                    },
                    {
                        "descriptor": {
                            "code": "CURRENT_PAGE_NUMBER"
                        },
                        "value": str(overall_page_number)
                    },
                    {
                        "descriptor": {
                            "code": "MAX_PAGE_NUMBER"
                        },
                        "value": str(total_pages)
                    }
                ]
            }
        ]

        # Log the final formatted data
        logging.info(f"Formatted ONDC Route stops data for page {overall_page_number}")

        # Send the formatted data to the BAP
        if bap_uri:
            status_code, response = post_request(bap_uri, formatted_data)
            logging.info(f"SEARCH_1 Response from BAP======: {status_code}, {response}")
            action = context_data['action']
            task_push_txn_logs.apply_async(args=[action, formatted_data])

            # If the request was successful, move to the next page
            if status_code == 200:
                next_page = overall_page_number + 1

                # Adjust offsets for next page and agency
                if current_agency == 'DTC':
                    if len(stops_data) < limit:
                        # Finished with DTC, switch to DIMTS
                        logging.info("Finished processing DTC data, switching to DIMTS.")
                        on_search_all_route_stops(context_data, page_number=1, limit=limit, dimts_offset=0, current_agency='DIMTS', overall_page_number=next_page)
                    else:
                        # Continue with DTC
                        on_search_all_route_stops(context_data, page_number=page_number + 1, limit=limit, dtc_offset=dtc_offset + limit, current_agency='DTC', overall_page_number=next_page)
                else:
                    if len(stops_data) < limit:
                        # Finished with DIMTS, stop the process
                        logging.info("Finished processing DIMTS data.")
                        return
                    else:
                        # Continue with DIMTS
                        on_search_all_route_stops(context_data, page_number=page_number + 1, limit=limit, dimts_offset=dimts_offset + limit, current_agency='DIMTS', overall_page_number=next_page)

    except psycopg2.Error as e:
        logging.error(f"Database error in on_search_all_route_stops: {e}")
    except ValueError as e:
        logging.error(f"Value error in on_search_all_route_stops: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in on_search_all_route_stops: {e}", exc_info=True)
