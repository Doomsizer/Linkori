from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser

class IsAuthenticated(permissions.BasePermission):
    """
    Разрешает доступ только аутентифицированным пользователям (по JWT)
    """
    def has_permission(self, request, view):
        return bool(request.user and not isinstance(request.user, AnonymousUser))

class IsLinked(permissions.BasePermission):
    """
    Разрешает доступ только пользователям с is_linked=True
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            not isinstance(request.user, AnonymousUser) and
            getattr(request.user, 'is_linked', False)
        )

class IsStaff(permissions.BasePermission):
    """
    Разрешает доступ только staff пользователям
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)