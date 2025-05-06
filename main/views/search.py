import logging
from datetime import datetime, timezone

from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from main.tasks.on_search import on_search
from main.tasks.ondc_all_route_search_ import on_search_all_route_stops
from main.tasks.task_send_no import task_push_txn_logs


class Search(mixins.CreateModelMixin, GenericViewSet):

    def create(self, request, *args, **kwargs):
        try:
            logging.info(f"search received at seller======={request.data}")
            if (request.data['context']['action'] != "search" or
                    request.data['context']['transaction_id'] is None or
                    request.data['message']['intent']['fulfillment']['vehicle']['category'] != "BUS"):
                raise Exception(f"Invalid data format ACTION: {request.data['context']['action']}, TXN_ID: {request.data['context']['transaction_id']},"
                                f"VEHICLE_CATEGORY: {request.data['message']['intent']['fulfillment']['vehicle']['category']}")
            transaction_id = request.data['context']['transaction_id']
            logging.info(f"search received at seller=======,{transaction_id},{datetime.now(timezone.utc)}")
            context = request.data['context']
            message = request.data['message']
            action = context['action']
            task_push_txn_logs.apply_async(args=[action, request.data])

            if message.get('intent', {}).get('fulfillment', {}).get('stops') is None:
                logging.info(f"Calling all routes search_1======{request.data}")
                on_search_all_route_stops.apply_async(args=[context])
                # search_all_route_stops(context)
                response = {'ack': True}
                return Response(response, status=200)

            stops = message['intent']['fulfillment']['stops']
            vehicle = message['intent']['fulfillment']['vehicle']

            on_search_request = {
                "context": context,
                "stops": stops,
                "vehicle": vehicle
            }
            if isinstance(stops, list) and len(stops) == 2:
                # Check if the first element is the start and the second is the end
                if stops[0].get('type') == "START" and stops[1].get('type') == "END":
                    # Queue the on_search in the background
                    logging.fatal(f"search scheduled from seller to celery,{transaction_id},{datetime.now(timezone.utc)}")
                    on_search.apply_async(args=[on_search_request])
                    # response = on_search(on_search_request)
                    # Return the acknowledgment response
                    return Response({"context": context, "message": {"ack": {"status": "ACK"}}}, status=200)
                else:
                    logging.error(
                        "Start stop or End stop not present or incorrectly specified")
                    return Response(
                        'Start stop or End stop not present or incorrectly specified',
                        status=400)
            else:
                logging.error("Incorrect number of stops provided")
                return Response('Incorrect number of stops provided', status=400)

        except Exception as e:
            logging.error(e)
            return Response({"message": {"ack": {"status": "NACK", "tags": str(e)}}}, status=400)
