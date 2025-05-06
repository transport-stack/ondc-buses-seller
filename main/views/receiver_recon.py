import logging
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from main.tasks.on_receiver_recon import on_receiver_recon


class ReceiverRecon(mixins.CreateModelMixin, GenericViewSet):

    def create(self, request, *args, **kwargs):
        try:
            if request.data.get('context', {}).get('action') != "receiver_recon":
                raise Exception("Invalid action. Expected 'receiver_recon'.")
            logging.info(f"inside receiver recon request.data================={request.data}")

            task_id = on_receiver_recon.apply_async(args=[request.data])
            logging.info(f"on_receiver_recon called========: {task_id}")

            return Response({"ack": {"status": "ACK"}}, status=200)

        except Exception as e:
            logging.error(str(e))
            return Response({"ack": {"status": "NACK", "tags": str(e)}}, status=400)
