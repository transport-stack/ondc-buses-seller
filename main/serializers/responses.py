from rest_framework import serializers

from main.serializers.requests import StopsSerializer, VehicleSerializer


class AdditionalDescSerializer(serializers.Serializer):
    url = serializers.CharField()
    content_type = serializers.CharField()


class MediaSerializer(serializers.Serializer):
    mimetype = serializers.CharField()
    url = serializers.CharField()
    signature = serializers.CharField()
    dsa = serializers.CharField()


class ImageSerializer(serializers.Serializer):
    url = serializers.CharField()
    size_type = serializers.CharField()
    width = serializers.CharField()
    height = serializers.CharField()


class DescriptorSerializer(serializers.Serializer):
    name = serializers.CharField()
    code = serializers.CharField()
    short_desc = serializers.CharField()
    long_desc = serializers.CharField()
    additional_desc = AdditionalDescSerializer()
    media = MediaSerializer(many=True)
    images = ImageSerializer(many=True)


class TagItemSerializer(serializers.Serializer):
    descriptor = DescriptorSerializer()
    value = serializers.CharField()
    display = serializers.BooleanField()


class TagSerializer(serializers.Serializer):
    display = serializers.BooleanField()
    descriptor = DescriptorSerializer()
    list = TagItemSerializer(many=True)


class AckSerializer(serializers.Serializer):
    status = serializers.CharField()
    tags = TagSerializer(many=True)


class MessageSerializer(serializers.Serializer):
    ack = AckSerializer()


class SearchResponseSerializer(serializers.Serializer):
    message = MessageSerializer()


# Search
class FulfilmentSerializer(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.CharField()
    stops = StopsSerializer()
    vehicle = VehicleSerializer()


class ProviderDescriptorSerializer(serializers.Serializer):
    name = serializers.CharField()


class ItemSerializer(serializers.Serializer):
    id = serializers.CharField()


class ItemsSerializer(serializers.Serializer):
    items = ItemSerializer(many=True)


class ProviderSerializer(serializers.Serializer):
    id = serializers.CharField()
    descriptor = ProviderDescriptorSerializer()
    fulfilments = FulfilmentSerializer(many=True)
    items = ItemsSerializer()


class ProvidersSerializer(serializers.Serializer):
    providers = ProviderSerializer(many=True)
