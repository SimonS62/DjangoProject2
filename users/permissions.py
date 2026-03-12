from rest_framework import permissions


class IsModerator(permissions.BasePermission):
    """
    Проверяет, является ли пользователь модератором.
    Модератор — это пользователь, состоящий в группе 'moderator'.
    """
    def has_permission(self, request, view):
        # Проверяем, состоит ли пользователь в группе 'moderator'
        return request.user.groups.filter(name='moderator').exists()

    # Если вам нужно проверять права на уровне объекта (например, редактировать конкретный урок)
    def has_object_permission(self, request, view, obj):
        # Для задач модерации, где предполагается работа с разными объектами,
        # чаще используется has_permission на уровне ViewSet,
        # но if you need object-level checks, you can add them here.
        # Например, модератор может редактировать любой урок, поэтому
        # has_object_permission может быть не так важен, как has_permission
        # для проверки группы.
        return request.user.groups.filter(name='moderator').exists()