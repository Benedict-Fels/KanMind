"""API views for boards, tasks and comments."""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from kanban_app.models import Board, Comment, Task
from .permissions import (IsBoardOwnerOrMember, IsCommentAuthor,
                          IsTaskBoardMember, TaskAccessPermission,
                          user_has_board_access)
from .serializers import (BoardDetailSerializer, BoardSerializer,
                          BoardUpdateSerializer, CommentSerializer,
                          TaskCreateSerializer, TaskUpdateSerializer,
                          TaskWithBoardSerializer, UserSerializer)


class EmailCheckView(APIView):
    """Look up a registered user by email address."""

    def get(self, request):
        """Return the user for ?email=..., otherwise 400 or 404."""
        email = request.query_params.get("email")

        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {"error": "A valid email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email=email).first()
        if user is None:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class BoardListCreateView(generics.ListCreateAPIView):
    """List the user's boards or create a new one."""

    serializer_class = BoardSerializer

    def get_queryset(self):
        """Return the boards the user owns or is a member of."""
        user = self.request.user
        owned_boards = Board.objects.filter(owner=user)
        member_boards = Board.objects.filter(members=user)
        return (owned_boards | member_boards).distinct()

    def perform_create(self, serializer):
        """Save the new board with the logged-in user as owner."""
        serializer.save(owner=self.request.user)


class TaskCreateView(generics.CreateAPIView):
    """Create a task on a board the user has access to."""

    serializer_class = TaskCreateSerializer

    def create(self, request):
        """Check the board (404) and access (403) before validating."""
        board_id = request.data.get("board")

        if type(board_id) is int:
            board = get_object_or_404(Board, id=board_id)
            if not user_has_board_access(board, request.user):
                raise PermissionDenied("You must be a member of this board.")
        return super().create(request)

    def perform_create(self, serializer):
        """Save the new task with the logged-in user as creator."""
        serializer.save(created_by=self.request.user)


class AssignedTaskListView(generics.ListAPIView):
    """List all tasks assigned to the logged-in user."""

    serializer_class = TaskWithBoardSerializer

    def get_queryset(self):
        """Return the tasks where the user is the assignee."""
        return Task.objects.filter(assignee=self.request.user)


class ReviewingTaskListView(generics.ListAPIView):
    """List all tasks the logged-in user has to review."""

    serializer_class = TaskWithBoardSerializer

    def get_queryset(self):
        """Return the tasks where the user is the reviewer."""
        return Task.objects.filter(reviewer=self.request.user)


class CommentListCreateView(generics.ListCreateAPIView):
    """List or create the comments of the task in the URL."""

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsTaskBoardMember]

    def get_queryset(self):
        """Return the comments of the task from the URL."""
        return Comment.objects.filter(task_id=self.kwargs["task_id"])

    def perform_create(self, serializer):
        """Save the comment with the logged-in user as author."""
        serializer.save(author=self.request.user,
                        task_id=self.kwargs["task_id"])


class CommentDeleteView(generics.DestroyAPIView):
    """Delete a comment. Only its author may do this."""

    permission_classes = [IsAuthenticated, IsTaskBoardMember, IsCommentAuthor]

    def get_queryset(self):
        """Only find comments that belong to the task in the URL."""
        return Comment.objects.filter(task_id=self.kwargs["task_id"])


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Show, update or delete a single board."""

    queryset = Board.objects.all()
    permission_classes = [IsAuthenticated, IsBoardOwnerOrMember]
    http_method_names = ["get", "patch", "delete", "options"]

    def get_serializer_class(self):
        """Use the update format for PATCH, the detail format otherwise."""
        if self.request.method == "PATCH":
            return BoardUpdateSerializer
        return BoardDetailSerializer


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Update or delete a single task."""

    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated, TaskAccessPermission]
    http_method_names = ["patch", "delete", "options"]
    serializer_class = TaskUpdateSerializer
