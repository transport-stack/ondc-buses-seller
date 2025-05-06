import logging
import os

from rest_framework import mixins
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from main.models import PassType
from main.tasks.on_init import on_init
from main.tasks.pass_on_init import pass_on_init
from main.utils.check_ttl import check_ttl
from main.tasks.task_send_no import task_push_txn_logs


class Init(mixins.CreateModelMixin, GenericViewSet):

    def create(self, request, *args, **kwargs):
        try:
            # ttl_check_response = check_ttl(request, "on_select")
            # if ttl_check_response is not None:
            #     return ttl_check_response
            # Check if the action in the context is 'init'
            if request.data.get('context', {}).get('action') != "init":
                raise Exception("Invalid action. Expected 'init'.")

            # Extracting context and message data
            context_data = request.data.get('context', {})
            message_data = request.data.get('message', {})
            order = message_data.get('order', {})
            action = context_data['action']
            task_push_txn_logs.apply_async(args=[action, request.data])

            # Adding a conditions to check if the context and message data are present
            if not context_data or not message_data or not order:
                raise ValidationError("Missing context or message data.")

            ALLOWED_BAP = os.getenv('ALLOWED_BAP', "")
            allowed_baps = None if ALLOWED_BAP in ["*", ""] else ALLOWED_BAP.split(',')

            if allowed_baps is not None and context_data.get('bap_id') not in allowed_baps:
                logging.info(f"Not allowed bap_id=========: {context_data.get('bap_id')}")
                return Response({"ack": {"status": "NACK", "tags": "BAP_ID not in allowed list"}}, status=400)

            request_data = {
                "context": context_data,
                "message": message_data
            }
            pass_type_ids = PassType.objects.values_list('item_id', 'provider_id')

            if (message_data['order']['items'][0]['id'], message_data['order']['provider']['id']) in pass_type_ids:
                print("pass_on_init=========")
                pass_on_init.apply_async(args=[request_data])
            else:
                print("on_init=========")
                on_init.apply_async(args=[request_data])

            return Response({"context": context_data, "message": {"ack": {"status": "ACK"}}}, status=200)

        except Exception as e:
            return Response({"message": {"ack": {"status": "NACK", "tags": str(e)}}}, status=400)
