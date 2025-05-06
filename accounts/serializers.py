from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import MyUser


class MyUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )

    class Meta:
        model = MyUser
        fields = (
            "id",
            "uuid",
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "phone",
        )
        read_only_fields = ("id", "uuid")

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
