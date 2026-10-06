from rest_framework import generics
from kanban_app.models import Board
from .serializers import BoardSerializer


class BoardListCreateView(generics.ListCreateAPIView):
    serializer_class = BoardSerializer

    def get_queryset(self):
        user = self.request.user
        owned_boards = Board.objects.filter(owner=user)
        member_boards = Board.objects.filter(members=user)
        return (owned_boards | member_boards).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
