"""Access rules for boards, tasks and comments."""

from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission

from kanban_app.models import Task


class IsBoardOwnerOrMember(BasePermission):
    """Owner and members may view and edit a board.

    Only the owner may delete it.
    """

    def has_object_permission(self, request, view, obj):
        """Only the owner may delete, owner and members may do the rest."""
        if request.method == "DELETE":
            return obj.owner_id == request.user.id
        return user_has_board_access(obj, request.user)


def user_has_board_access(board, user):
    """Return True if the user owns the board or is one of its members."""
    return (
        board.owner_id == user.id
        or board.members.filter(id=user.id).exists()
    )


class TaskAccessPermission(BasePermission):
    """Everyone with access to the board may edit a task.

    Only the task creator or the board owner may delete it.
    """

    def has_object_permission(self, request, view, obj):
        """Creator or board owner may delete, board users may edit."""
        if request.method == "DELETE":
            is_creator = obj.created_by_id == request.user.id
            is_board_owner = obj.board.owner_id == request.user.id
            return is_creator or is_board_owner
        return user_has_board_access(obj.board, request.user)


class IsTaskBoardMember(BasePermission):
    """Only users with access to the task's board may read
    or write its comments.
    """

    def has_permission(self, request, view):
        """Load the task from the URL (404), then check access (403)."""
        task = get_object_or_404(Task, id=view.kwargs["task_id"])
        return user_has_board_access(task.board, request.user)


class IsCommentAuthor(BasePermission):
    """Only the author of a comment may delete it."""

    def has_object_permission(self, request, view, comment):
        """Return True if the logged-in user wrote the comment."""
        return comment.author_id == request.user.id
