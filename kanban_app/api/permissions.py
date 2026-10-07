from rest_framework.permissions import BasePermission


class IsBoardOwnerOrMember(BasePermission):
    """Owner and members may view and edit a board. Only the owner may delete it."""

    def has_object_permission(self, request, view, obj):
        is_owner = obj.owner == request.user
        is_member = obj.members.filter(id=request.user.id).exists()
        if request.method == "DELETE":
            return is_owner
        return is_owner or is_member
