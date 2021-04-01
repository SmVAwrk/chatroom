from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """Кастомные права доступа. Доступ только для владельца или админа."""

    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated
                    and (request.user == obj.owner or request.user.is_staff))


class IsOwnerOrMember(BasePermission):
    """Кастомные права доступа. Доступ только для участников."""

    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated
                    and (request.user in obj.members.all() or request.user == obj.owner))
