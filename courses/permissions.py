from rest_framework import permissions


class IsOwnerOrStaff(permissions.BasePermission):
    """Разрешение только для владельца или персонала"""

    def has_object_permission(self, request, view, obj):
        # Разрешаем персоналу
        if request.user.is_staff:
            return True

        # Проверяем владельца
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        return False