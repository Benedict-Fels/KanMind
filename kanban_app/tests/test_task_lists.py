from django.urls import reverse
from rest_framework import status

from kanban_app.tests.test_boards import BoardTestCase


class TaskListTestCase(BoardTestCase):
    """Adds three tasks: one assigned to the member, one to the owner, one to nobody."""

    def setUp(self):
        super().setUp()
        self.member_task = self.create_task("to-do", "high")
        self.member_task.assignee = self.member
        self.member_task.reviewer = self.owner
        self.member_task.save()
        self.owner_task = self.create_task("done", "low")
        self.owner_task.assignee = self.owner
        self.owner_task.save()
        self.free_task = self.create_task("review", "medium")


class AssignedToMeTests(TaskListTestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse("tasks-assigned-to-me")

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_only_tasks_assigned_to_user(self):
        self.authenticate(self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task_ids = [task["id"] for task in response.data]
        self.assertEqual(task_ids, [self.member_task.id])

    def test_task_contains_board_id(self):
        self.authenticate(self.member)
        task_data = self.client.get(self.url).data[0]
        self.assertEqual(task_data["board"], self.board.id)
        self.assertEqual(task_data["assignee"]["id"], self.member.id)


class ReviewingTests(TaskListTestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse("tasks-reviewing")

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_only_tasks_reviewed_by_user(self):
        self.authenticate(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task_ids = [task["id"] for task in response.data]
        self.assertEqual(task_ids, [self.member_task.id])

    def test_user_without_review_tasks_gets_empty_list(self):
        self.authenticate(self.member)
        response = self.client.get(self.url)
        self.assertEqual(response.data, [])


class TaskListUrlTests(TaskListTestCase):

    def test_urls_match_the_docs(self):
        self.assertEqual(reverse("tasks-assigned-to-me"), "/api/tasks/assigned-to-me/")
        self.assertEqual(reverse("tasks-reviewing"), "/api/tasks/reviewing/")
