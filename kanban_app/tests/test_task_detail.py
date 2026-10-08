from django.urls import reverse
from rest_framework import status

from kanban_app.models import Board, Task
from kanban_app.tests.test_boards import BoardTestCase, create_user


class TaskDetailTestCase(BoardTestCase):
    """A task created by the member,
    plus a second member who did not create it."""

    def setUp(self):
        super().setUp()
        self.other_member = create_user("other@test.de")
        self.board.members.add(self.other_member)
        self.task = self.create_task("to-do", "high")
        self.task.created_by = self.member
        self.task.save()

    def detail_url(self, task_id=None):
        return reverse("task-detail", kwargs={"pk": task_id or self.task.id})


class TaskDeleteTests(TaskDetailTestCase):

    def test_requires_authentication(self):
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_creator_can_delete_task(self):
        self.authenticate(self.member)
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_board_owner_can_delete_task(self):
        self.authenticate(self.owner)
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_other_member_cannot_delete_task(self):
        self.authenticate(self.other_member)
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Task.objects.filter(id=self.task.id).exists())

    def test_outsider_cannot_delete_task(self):
        self.authenticate(self.outsider)
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_task_returns_404(self):
        self.authenticate(self.owner)
        response = self.client.delete(self.detail_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_task_without_creator_can_be_deleted_by_owner(self):
        self.task.created_by = None
        self.task.save()
        self.authenticate(self.owner)
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_task_without_creator_cannot_be_deleted_by_member(self):
        self.task.created_by = None
        self.task.save()
        self.authenticate(self.member)
        response = self.client.delete(self.detail_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_is_not_allowed(self):
        self.authenticate(self.owner)
        response = self.client.get(self.detail_url())
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)


class TaskPatchTests(TaskDetailTestCase):

    def patch_task(self, data, task_id=None):
        return self.client.patch(self.detail_url(task_id), data, format="json")

    def test_member_can_update_task(self):
        self.authenticate(self.other_member)
        response = self.patch_task({"status": "done"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "done")

    def test_response_contains_exactly_the_documented_fields(self):
        self.authenticate(self.member)
        response = self.patch_task({"title": "Changed"})
        expected_fields = {
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
        }
        self.assertEqual(set(response.data.keys()), expected_fields)

    def test_only_sent_fields_are_changed(self):
        self.authenticate(self.member)
        self.patch_task({"title": "Changed"})
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Changed")
        self.assertEqual(self.task.status, "to-do")
        self.assertEqual(self.task.priority, "high")

    def test_assignee_can_be_changed(self):
        self.authenticate(self.member)
        response = self.patch_task({"assignee_id": self.other_member.id})
        self.assertEqual(response.data["assignee"]["id"], self.other_member.id)

    def test_outsider_as_assignee_returns_400(self):
        self.authenticate(self.member)
        response = self.patch_task({"assignee_id": self.outsider.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assignee_id", response.data)

    def test_outsider_cannot_update_task(self):
        self.authenticate(self.outsider)
        response = self.patch_task({"title": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Test Task")

    def test_unknown_task_returns_404(self):
        self.authenticate(self.member)
        response = self.patch_task({"title": "Changed"}, task_id=9999)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_changing_board_returns_400(self):
        other_board = Board.objects.create(title="Other Board",
                                           owner=self.member)
        self.authenticate(self.member)
        response = self.patch_task({"board": other_board.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("board", response.data)
        self.task.refresh_from_db()
        self.assertEqual(self.task.board, self.board)

    def test_sending_same_board_is_allowed(self):
        self.authenticate(self.member)
        data = {"board": self.board.id, "title": "Changed"}
        response = self.patch_task(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
