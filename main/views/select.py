import logging
from datetime import datetime, timezone

from rest_framework import mixins
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from main.models import PassType
from main.tasks.on_select import on_select
from main.tasks.pass_on_select import pass_on_select
from main.utils.check_ttl import check_ttl
from main.tasks.task_send_no import task_push_txn_logs


class Select(mixins.CreateModelMixin, GenericViewSet):

    def create(self, request, *args, **kwargs):
        try:
            # ttl_check_response = check_ttl(request, "on_search")
            # if ttl_check_response is not None:
            #     return ttl_check_response
            if request.data['context']['action'] != "select":
                raise Exception("Invalid action")
            try:
                context = request.data['context']
                transaction_id = request.data['context']['transaction_id']
                logging.fatal(f"select received at seller,{transaction_id},{datetime.now(timezone.utc)}")
                item = request.data['message']['order']['items']
                provider = request.data['message']['order']['provider']
                action = context['action']
                task_push_txn_logs.apply_async(args=[action, request.data])

                if not (context or item or provider):
                    raise Exception(
                        "Missing required fields in the request data.")
            except (KeyError, TypeError) as e:
                raise Exception(f"Invalid request format, Missing key: {e}")

            on_select_request = {
                "context": context,
                "item": item,
                "provider": provider,
            }
            logging.fatal(f"select scheduled from seller to celery,{transaction_id},{datetime.now(timezone.utc)}")

            pass_type_ids = PassType.objects.values_list('item_id', 'provider_id')

            if (item[0]['id'], provider['id']) in pass_type_ids:
                pass_on_select.apply_async(args=[on_select_request])
            else:
                on_select.apply_async(args=[on_select_request])
                # on_select(on_select_request)

            return Response({"context": context, "message": {"ack": {"status": "ACK"}}}, status=200)
        except Exception as e:
            return Response({"context": context, "message": {"ack": {"status": "NACK", "tags": str(e)}}}, status=400)
