from django.utils.timezone import localtime
from rest_framework import serializers
from main.models.tickets import (
    Ticket, TicketType, Agency, FareBreakup, TicketUpdate
)


class FareBreakupSerializer(serializers.ModelSerializer):
    class Meta:
        model = FareBreakup
        fields = '__all__'


class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = '__all__'


class TicketTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketType
        fields = '__all__'


class TicketUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketUpdate
        fields = '__all__'


class TicketSerializer(serializers.ModelSerializer):
    fare = FareBreakupSerializer(required=False, allow_null=True)
    agency = AgencySerializer(required=False, allow_null=True)
    ticket_type = TicketTypeSerializer()
    ticket_updates = TicketUpdateSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        valid_till = instance.valid_till
        # Rename the fields in the serialized output.
        valid_till_local = localtime(valid_till)
        formatted_dt = valid_till_local.strftime("%Y-%m-%dT%H:%M:%S.%f")
        formatted_offset = valid_till_local.strftime("%z")
        # Insert colon in timezone offset (e.g., +05:30)
        formatted_offset = formatted_offset[:3] + ":" + formatted_offset[3:]
        representation['valid_till'] = formatted_dt + formatted_offset
        representation['status'] = representation.pop('ticket_status')
        representation['start_location_name'] = representation.pop('start_stop_name')
        representation['end_location_name'] = representation.pop('end_stop_name')
        return representation

