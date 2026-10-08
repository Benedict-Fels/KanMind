from django.http import request
from rest_framework.permissions import BasePermission


class IsBoardOwnerOrMember(BasePermission):
    """Owner and members may view and edit a board. Only the owner may delete it."""

    def has_object_permission(self, request, view, obj):
        if request.method == "DELETE":
            return obj.owner == request.user
        return obj.user_has_access(request.user)
