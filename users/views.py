from rest_framework import viewsets,permissions
from rest_framework.generics import CreateAPIView
from users.models import User
from users.serializers import UserProfileSerializer, RegisterSerializer


# Эндпоинт для регистрации
class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с пользователями"""
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            # Разрешаем создание всем? Нет, по заданию только регистрация.
            # CRUD для пользователей обычно закрыт, кроме аутентифицированных.
            # Оставим IsAuthenticated, если нужно, чтобы только аутентифицированные могли создавать/редактировать
            # Для регистрации у нас отдельный эндпоинт.
            self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'list':
             self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'retrieve':
             self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'update':
             self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'partial_update':
             self.permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'destroy':
             self.permission_classes = [permissions.IsAuthenticated]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in self.permission_classes]
