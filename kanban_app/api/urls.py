from django.urls import path
from .views import AssignedTaskListView, BoardDetailView, BoardListCreateView, EmailCheckView, ReviewingTaskListView

urlpatterns = [
    path("boards/", BoardListCreateView.as_view(), name="board-list"),
    path("email-check/", EmailCheckView.as_view(), name="email-check"),
    path("boards/<int:pk>/", BoardDetailView.as_view(), name="board-detail"),
    path("tasks/assigned-to-me/", AssignedTaskListView.as_view(), name="tasks-assigned-to-me"),
    path("tasks/reviewing/", ReviewingTaskListView.as_view(), name="tasks-reviewing"),
]
