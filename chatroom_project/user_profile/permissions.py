from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """Кастомные права доступа. Доступ только для владельца или админа."""

    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated
                    and (request.user == obj.user or request.user.is_staff))
