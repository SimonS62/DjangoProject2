from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from users.models import User
from users.serializers import UserProfileSerializer


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с пользователями"""
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]  # Регистрация доступна всем
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
