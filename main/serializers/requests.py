from rest_framework import serializers


# Init
class ItemQuantitySerializer(serializers.Serializer):
    count = serializers.IntegerField()


class SelectedQuantitySerializer(serializers.Serializer):
    selected = ItemQuantitySerializer()


class ItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    quantity = SelectedQuantitySerializer()


class ProviderSerializer(serializers.Serializer):
    id = serializers.CharField()


class BillingSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()


class PaymentSerializer(serializers.Serializer):
    collected_by = serializers.CharField()
    status = serializers.CharField()
    type = serializers.CharField()


class OrderSerializer(serializers.Serializer):
    items = ItemSerializer(many=True)
    provider = ProviderSerializer()
    billing = BillingSerializer()
    payments = PaymentSerializer(many=True)


# Search
class LocationDescriptorSerializer(serializers.Serializer):
    name = serializers.CharField()
    code = serializers.CharField()


class LocationSerializer(serializers.Serializer):
    gps = serializers.CharField()
    descriptor = LocationDescriptorSerializer()


class StopSerializer(serializers.Serializer):
    type = serializers.CharField()
    location = LocationSerializer()


class StopsSerializer(serializers.Serializer):
    stops = StopSerializer(many=True)


class VehicleSerializer(serializers.Serializer):
    category = serializers.CharField()


# Select
class SelectedSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class QuantitySerializer(serializers.Serializer):
    selected = SelectedSerializer()


class ItemsSerializer(serializers.Serializer):
    items = ItemSerializer(many=True)
