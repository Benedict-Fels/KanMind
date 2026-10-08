from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404

from .permissions import IsBoardOwnerOrMember, TaskAccessPermission
from kanban_app.models import Board, Comment, Task
from .serializers import BoardSerializer, BoardUpdateSerializer, CommentSerializer, TaskCreateSerializer, TaskUpdateSerializer, TaskWithBoardSerializer, UserSerializer, BoardDetailSerializer


class EmailCheckView(APIView):

    def get(self, request):
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
    serializer_class = BoardSerializer

    def get_queryset(self):
        user = self.request.user
        owned_boards = Board.objects.filter(owner=user)
        member_boards = Board.objects.filter(members=user)
        return (owned_boards | member_boards).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class TaskCreateView(generics.CreateAPIView):
    serializer_class = TaskCreateSerializer

    def create(self, request):
        board_id = request.data.get("board")

        if type(board_id) is int:
            board = get_object_or_404(Board, id=board_id)
            if not board.user_has_access(request.user):
                raise PermissionDenied("You must be a member of this board.")
        return super().create(request)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class AssignedTaskListView(generics.ListAPIView):
    serializer_class = TaskWithBoardSerializer

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user)


class ReviewingTaskListView(generics.ListAPIView):
    serializer_class = TaskWithBoardSerializer

    def get_queryset(self):
        return Task.objects.filter(reviewer=self.request.user)


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        return Comment.objects.filter(task_id=self.kwargs["task_id"])

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, task_id=self.kwargs["task_id"])


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Board.objects.all()
    permission_classes = [IsAuthenticated, IsBoardOwnerOrMember]
    http_method_names = ["get", "patch", "delete", "options"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return BoardUpdateSerializer
        return BoardDetailSerializer


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated, TaskAccessPermission]
    http_method_names = ["patch", "delete", "options"]
    serializer_class = TaskUpdateSerializer
