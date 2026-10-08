from django.urls import reverse
from rest_framework import status

from kanban_app.models import Task
from kanban_app.tests.test_boards import BoardTestCase, create_user


class TaskDetailTestCase(BoardTestCase):
    """A task created by the member, plus a second member who did not create it."""

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
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
