from django.http import request
from rest_framework.permissions import BasePermission


class IsBoardOwnerOrMember(BasePermission):
    """Owner and members may view and edit a board. Only the owner may delete it."""

    def has_object_permission(self, request, view, obj):
        if request.method == "DELETE":
            return obj.owner == request.user
        return obj.user_has_access(request.user)


class TaskAccessPermission(BasePermission):
    """Everyone with access to the board may edit a task.
    Only the task creator or the board owner may delete it."""

    def has_object_permission(self, request, view, obj):
        if request.method == "DELETE":
            is_creator = obj.created_by_id == request.user.id
            is_board_owner = obj.board.owner_id == request.user.id
            return is_creator or is_board_owner
        return obj.board.user_has_access(request.user)
