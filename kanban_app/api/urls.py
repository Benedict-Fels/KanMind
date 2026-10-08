from django.urls import path
from .views import (AssignedTaskListView, BoardDetailView,
                    BoardListCreateView, CommentDeleteView,
                    CommentListCreateView, EmailCheckView,
                    ReviewingTaskListView, TaskCreateView,
                    TaskDetailView)

urlpatterns = [
    path("boards/", BoardListCreateView.as_view(), name="board-list"),
    path("email-check/", EmailCheckView.as_view(), name="email-check"),
    path("boards/<int:pk>/", BoardDetailView.as_view(), name="board-detail"),
    path("tasks/assigned-to-me/", AssignedTaskListView.as_view(),
         name="tasks-assigned-to-me"),
    path("tasks/reviewing/", ReviewingTaskListView.as_view(),
         name="tasks-reviewing"),
    path("tasks/", TaskCreateView.as_view(), name="task-create"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path("tasks/<int:task_id>/comments/", CommentListCreateView.as_view(),
         name="comment-list"),
    path("tasks/<int:task_id>/comments/<int:pk>/", CommentDeleteView.as_view(),
         name="comment-detail",)
]
