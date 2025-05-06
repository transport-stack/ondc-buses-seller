from rest_framework import serializers
from main.models.pass_setup import Pass, PassFareBreakup, PassType
from main.models.tickets import Agency
from django.utils.timezone import localtime


class PassFareBreakupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassFareBreakup
        fields = '__all__'


class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = '__all__'


class PassTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassType
        fields = '__all__'


class PassSerializer(serializers.ModelSerializer):
    fare = PassFareBreakupSerializer(required=False, allow_null=True)
    agency = AgencySerializer(required=False, allow_null=True)
    pass_type = PassTypeSerializer()

    class Meta:
        model = Pass
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        valid_till = instance.valid_till
        # Convert to local time (assumes Django settings.TIME_ZONE is set correctly)
        valid_till_local = localtime(valid_till)
        formatted_dt = valid_till_local.strftime("%Y-%m-%dT%H:%M:%S.%f")
        formatted_offset = valid_till_local.strftime("%z")
        # Insert colon in timezone offset (e.g., +05:30)
        formatted_offset = formatted_offset[:3] + ":" + formatted_offset[3:]
        representation['valid_till'] = formatted_dt + formatted_offset
        representation['status'] = representation.pop('pass_status')
        return representation


