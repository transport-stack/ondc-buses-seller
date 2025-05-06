import logging
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers, status, viewsets
from rest_framework.response import Response

from main.models import Pass, Ticket
from main.models.pass_serializer import PassSerializer
from main.models.ticket_serializer import TicketSerializer
from modules.ticket_string_generator.main import decrypt_with_salt


# A simple serializer for input validation
class ValidateQRSerializer(serializers.Serializer):
    qr_string = serializers.CharField(required=True)


class ValidateQRString(viewsets.GenericViewSet):
    serializer_class = ValidateQRSerializer

    def create(self, request, *args, **kwargs):
        # Validate the input data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        qr_string = serializer.validated_data.get("qr_string")

        response_object = {"ticket": None, "pass": None}

        if not qr_string:
            logging.error("QR string is empty.")
            return Response({"detail": "Empty QR string"}, status=status.HTTP_400_BAD_REQUEST)

        # Attempt to decrypt the QR string
        try:
            transit_data = decrypt_with_salt(qr_string)
        except Exception as e:
            logging.error(f"Error in decrypting qr_string: {e}")
            return Response({"message": "failure", "description": f"Invalid QR code: {e}", "data": None}, status=status.HTTP_400_BAD_REQUEST)

        # Process the 'pass' key if present
        if "pass" in transit_data:
            try:
                bus_pass = Pass.objects.get(pnr=transit_data["pass"])
                response_object["pass"] = PassSerializer(bus_pass).data
            except ObjectDoesNotExist:
                logging.error(f"No Pass found for PNR: {transit_data['pass']}")
                response_object["pass"] = None

        # Process the 'ticket' key if present
        if "ticket" in transit_data:
            try:
                ticket_obj = Ticket.objects.get(pnr=transit_data["ticket"])
                response_object["ticket"] = TicketSerializer(ticket_obj).data
            except ObjectDoesNotExist:
                logging.error(f"No Ticket found for PNR: {transit_data['ticket']}")
                response_object["ticket"] = None

        # If neither Pass nor Ticket is found, return an error response
        if not response_object.get("pass") and not response_object.get("ticket"):
            logging.warning("Neither 'pass' nor 'ticket' found in transit_data")
            return Response({"message": "failure", "description": "Invalid QR data", "data": None}, status=status.HTTP_400_BAD_REQUEST)
        key = list(transit_data.keys())[0]
        final_response = {
            "message": "success",
            "description": f"{key} data found successfully",
            "data": response_object
        }
        return Response(final_response)
