"""Database models for boards, tasks and comments."""

from django.contrib.auth.models import User
from django.db import models


class Board(models.Model):
    """A Kanban board with an owner and any number of members."""

    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_boards"
    )
    members = models.ManyToManyField(User, related_name="boards", blank=True)

    def __str__(self):
        """Return the board title."""
        return self.title


class Task(models.Model):
    """A task on a board, optionally with assignee and reviewer."""

    STATUS_CHOICES = [
        ("to-do", "To do"),
        ("in-progress", "In progress"),
        ("review", "Review"),
        ("done", "Done"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    board = models.ForeignKey(Board, on_delete=models.CASCADE,
                              related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    assignee = models.ForeignKey(User, related_name="assigned_tasks",
                                 on_delete=models.SET_NULL, null=True,
                                 blank=True)
    reviewer = models.ForeignKey(User, related_name="review_tasks",
                                 on_delete=models.SET_NULL, null=True,
                                 blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_tasks",
                                   on_delete=models.SET_NULL, null=True)

    def __str__(self):
        """Return the task title."""
        return self.title


class Comment(models.Model):
    """A comment written by a user on a task."""

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        """Return a short description for the admin."""
        return f"Comment by {self.author.username} on {self.task.title}"
