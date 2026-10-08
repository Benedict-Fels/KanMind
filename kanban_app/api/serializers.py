"""Serializers that turn boards, tasks and comments into JSON and back."""

from django.contrib.auth.models import User
from rest_framework import serializers

from .permissions import user_has_board_access

from kanban_app.models import Board, Comment, Task


class UserSerializer(serializers.ModelSerializer):
    """Basic user data (id, email, full name) for nested responses."""

    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]

    def get_fullname(self, obj):
        """Return the user's first and last name."""
        return obj.get_full_name()


class BoardSerializer(serializers.ModelSerializer):
    """Board list format with counters, used by GET/POST /boards/."""

    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ["id",
                  "title",
                  "members",
                  "member_count",
                  "ticket_count",
                  "tasks_to_do_count",
                  "tasks_high_prio_count",
                  "owner_id"]
        extra_kwargs = {"members": {"write_only": True}}

    def get_member_count(self, obj):
        """Return the number of board members."""
        return obj.members.count()

    def get_ticket_count(self, obj):
        """Return the number of tasks on the board."""
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """Return the number of tasks with status 'to-do'."""
        return obj.tasks.filter(status="to-do").count()

    def get_tasks_high_prio_count(self, obj):
        """Return the number of tasks with priority 'high'."""
        return obj.tasks.filter(priority="high").count()


class TaskSerializer(serializers.ModelSerializer):
    """Task with nested assignee and reviewer, used in board details."""

    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ["id",
                  "title",
                  "description",
                  "status",
                  "priority",
                  "assignee",
                  "reviewer",
                  "due_date",
                  "comments_count"]

    def get_comments_count(self, obj):
        """Return the number of comments on the task."""
        return obj.comments.count()


class TaskWithBoardSerializer(TaskSerializer):
    """Task format including the board id, used for task lists."""

    class Meta(TaskSerializer.Meta):
        fields = ["id",
                  "board",
                  "title",
                  "description",
                  "status",
                  "priority",
                  "assignee",
                  "reviewer",
                  "due_date",
                  "comments_count"]


class CommentSerializer(serializers.ModelSerializer):
    """Comment with the author's full name as plain text."""

    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]

    def get_author(self, comment):
        """Return the full name of the comment's author."""
        return comment.author.get_full_name()


class TaskCreateSerializer(TaskWithBoardSerializer):
    """Create a task. Users are written as ids, read as objects."""

    assignee_id = serializers.PrimaryKeyRelatedField(
        source="assignee",
        queryset=User.objects.all(),
        write_only=True,
        allow_null=True,
        required=False,
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        source="reviewer",
        queryset=User.objects.all(),
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta(TaskWithBoardSerializer.Meta):
        fields = TaskWithBoardSerializer.Meta.fields + [
            "assignee_id",
            "reviewer_id",
        ]

    def validate(self, data):
        """Run all cross-field checks and report every error at once."""
        board = self.get_task_board(data)
        errors = self.get_board_change_errors(data)
        errors.update(self.get_access_errors(data, board))
        if errors:
            raise serializers.ValidationError(errors)
        return data

    def get_task_board(self, data):
        """Return the current board on update, the requested one on create."""
        if self.instance:
            return self.instance.board
        return data["board"]

    def get_board_change_errors(self, data):
        """Return an error if an update tries to move the task."""
        if not self.instance or "board" not in data:
            return {}
        if data["board"] != self.instance.board:
            return {"board": "The board of a task cannot be changed."}
        return {}

    def get_access_errors(self, data, board):
        """Return errors for an assignee or reviewer without board access."""
        errors = {}
        for field in ("assignee", "reviewer"):
            user = data.get(field)
            if user and not user_has_board_access(board, user):
                errors[f"{field}_id"] = (
                    f"{field.capitalize()} must be a member of the board."
                )
        return errors


class TaskUpdateSerializer(TaskCreateSerializer):
    """Update a task. The response has no board or comments_count."""

    class Meta(TaskCreateSerializer.Meta):
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "assignee_id",
            "reviewer_id",
            "due_date",
        ]
        extra_kwargs = {"board": {"write_only": True}}


class BoardDetailSerializer(serializers.ModelSerializer):
    """Board details with nested members and tasks (GET)."""

    members = UserSerializer(many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]


class BoardUpdateSerializer(serializers.ModelSerializer):
    """Update title and members, respond with owner/members data."""

    owner_data = UserSerializer(source="owner", read_only=True)
    members_data = UserSerializer(source="members", many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "members", "owner_data", "members_data"]
        extra_kwargs = {"members": {"write_only": True}}
