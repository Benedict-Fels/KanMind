from rest_framework import serializers
from kanban_app.models import Board, Task
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]

    def get_fullname(self, obj):
        return obj.get_full_name()


class BoardSerializer(serializers.ModelSerializer):
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
        return obj.members.count()

    def get_ticket_count(self, obj):
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status="to-do").count()

    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(priority="high").count()


class TaskSerializer(serializers.ModelSerializer):
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
        return obj.comments.count()


class TaskWithBoardSerializer(TaskSerializer):

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


class BoardDetailSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]


class BoardUpdateSerializer(serializers.ModelSerializer):
    owner_data = UserSerializer(source="owner", read_only=True)
    members_data = UserSerializer(source="members", many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "members", "owner_data", "members_data"]
        extra_kwargs = {"members": {"write_only": True}}
