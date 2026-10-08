from django.urls import reverse
from rest_framework import status

from kanban_app.models import Task
from kanban_app.tests.test_boards import BoardTestCase


class TaskCreateTestCase(BoardTestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse("task-create")

    def valid_data(self, **changes):
        data = {
            "board": self.board.id,
            "title": "New Task",
            "description": "Some description",
            "status": "to-do",
            "priority": "high",
            "assignee_id": self.member.id,
            "reviewer_id": None,
            "due_date": "2026-12-31",
        }
        data.update(changes)
        return data

    def post_task(self, data):
        return self.client.post(self.url, data, format="json")


class TaskCreateBasicTests(TaskCreateTestCase):

    def test_requires_authentication(self):
        response = self.post_task(self.valid_data())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_can_create_task(self):
        self.authenticate(self.member)
        response = self.post_task(self.valid_data())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["board"], self.board.id)
        self.assertEqual(response.data["assignee"]["id"], self.member.id)
        self.assertIsNone(response.data["reviewer"])
        self.assertEqual(response.data["comments_count"], 0)

    def test_response_contains_exactly_the_documented_fields(self):
        self.authenticate(self.member)
        response = self.post_task(self.valid_data())
        expected_fields = {
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        }
        self.assertEqual(set(response.data.keys()), expected_fields)

    def test_created_by_is_logged_in_user(self):
        self.authenticate(self.member)
        response = self.post_task(self.valid_data())
        task = Task.objects.get(id=response.data["id"])
        self.assertEqual(task.created_by, self.member)

    def test_task_without_assignee_and_reviewer(self):
        self.authenticate(self.member)
        response = self.post_task(self.valid_data(assignee_id=None))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["assignee"])

    def test_invalid_status_returns_400(self):
        self.authenticate(self.member)
        response = self.post_task(self.valid_data(status="almost-done"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_missing_title_returns_400(self):
        self.authenticate(self.member)
        data = self.valid_data()
        del data["title"]
        response = self.post_task(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)


class TaskCreateMemberRuleTests(TaskCreateTestCase):

    def test_outsider_as_assignee_returns_400(self):
        self.authenticate(self.member)
        response = self.post_task(self.valid_data(assignee_id=self.outsider.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assignee_id", response.data)

    def test_outsider_as_reviewer_returns_400(self):
        self.authenticate(self.member)
        response = self.post_task(self.valid_data(reviewer_id=self.outsider.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reviewer_id", response.data)

    def test_owner_can_be_assignee_without_being_member(self):
        self.authenticate(self.member)
        response = self.post_task(self.valid_data(assignee_id=self.owner.id))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["assignee"]["id"], self.owner.id)

    def test_no_task_is_created_on_400(self):
        self.authenticate(self.member)
        self.post_task(self.valid_data(assignee_id=self.outsider.id))
        self.assertFalse(Task.objects.exists())


class TaskCreateBoardAccessTests(TaskCreateTestCase):

    def test_unknown_board_returns_404(self):
        self.authenticate(self.member)
        response = self.post_task(self.valid_data(board=9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_cannot_create_task(self):
        self.authenticate(self.outsider)
        response = self.post_task(self.valid_data(assignee_id=None))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Task.objects.exists())

    def test_owner_without_membership_can_create_task(self):
        self.authenticate(self.owner)
        response = self.post_task(self.valid_data())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_missing_board_returns_400(self):
        self.authenticate(self.member)
        data = self.valid_data()
        del data["board"]
        response = self.post_task(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("board", response.data)

    def test_board_as_text_returns_400(self):
        self.authenticate(self.member)
        response = self.post_task(self.valid_data(board="abc"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
