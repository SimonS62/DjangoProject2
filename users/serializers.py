from rest_framework import serializers
from django.contrib.auth import get_user_model


User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Добавляем новые поля для редактирования
        fields = ("id", "email", "first_name", "last_name", "phone", "city", "avatar")
        read_only_fields = (
            "email",
            "id",
        )  # Email и ID не должны редактироваться через этот endpoint
