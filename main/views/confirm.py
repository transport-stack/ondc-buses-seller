import logging
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from main.models import PassType
from main.tasks.pass_on_confirm import pass_on_confirm
# from main.tasks.on_confirm import on_confirm
from main.tasks.on_confirm_wo_bus import on_confirm
from main.utils.check_ttl import check_ttl
from main.tasks.task_send_no import task_push_txn_logs


# The customer wants to confirm a particular route
class Confirm(mixins.CreateModelMixin, GenericViewSet):

    def create(self, request, *args, **kwargs):
        try:
            # ttl_check_response = check_ttl(request, "on_init")
            # if ttl_check_response is not None:
            #     return ttl_check_response
            # Validate the request payload
            if request.data.get('context', {}).get('action') != "confirm":
                raise Exception("Invalid action. Expected 'confirm'.")
            # Extracting context and message data
            context_data = request.data.get('context', {})
            message_data = request.data.get('message', {})
            action = context_data['action']
            task_push_txn_logs.apply_async(args=[action, request.data])
            # Validate the request payload and payment key
            if not context_data or not message_data['order'] or 'payments' not in message_data['order']:
                print("Transaction_id========", message_data['order']['payments'][0]['params'])
                raise Exception("Missing context or message data.")
            elif 'transaction_id' not in message_data['order']['payments'][0]['params']:
                raise Exception("Missing payment transaction ID")
            else:
                request_data = {
                    "context": context_data,
                    "message": message_data
                }
                pass_type_ids = PassType.objects.values_list('item_id', 'provider_id')

                if (message_data['order']['items'][0]['id'], message_data['order']['provider']['id']) in pass_type_ids:
                    pass_on_confirm.apply_async(args=[request_data])
                else:
                    on_confirm.apply_async(args=[request_data])

            return Response({"context": context_data, "message": {"ack": {"status": "ACK"}}}, status=200)

        except Exception as e:
            logging.error(str(e))
            return Response({"message": {"ack": {"status": "NACK", "tags": str(e)}}}, status=400)
