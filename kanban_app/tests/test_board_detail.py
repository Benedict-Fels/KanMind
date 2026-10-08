from django.urls import reverse
from rest_framework import status

from kanban_app.models import Board, Comment, Task
from kanban_app.tests.test_boards import BoardTestCase


class BoardDetailTestCase(BoardTestCase):
    """Adds the detail URL helper to the shared board setup."""

    def detail_url(self, board_id):
        return reverse("board-detail", kwargs={"pk": board_id})


class BoardDetailGetTests(BoardDetailTestCase):

    def test_requires_authentication(self):
        response = self.client.get(self.detail_url(self.board.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_board_with_nested_members(self):
        self.authenticate(self.owner)
        response = self.client.get(self.detail_url(self.board.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.board.id)
        self.assertEqual(response.data["title"], "Test Board")
        self.assertEqual(response.data["owner_id"], self.owner.id)
        member = response.data["members"][0]
        self.assertEqual(member["id"], self.member.id)
        self.assertEqual(set(member.keys()), {"id", "email", "fullname"})

    def test_unknown_board_returns_404(self):
        self.authenticate(self.owner)
        response = self.client.get(self.detail_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_returns_nested_tasks(self):
        task = self.create_task("to-do", "high")
        task.assignee = self.member
        task.save()
        Comment.objects.create(task=task, author=self.member,
                               content="Looks good")
        self.authenticate(self.owner)
        response = self.client.get(self.detail_url(self.board.id))
        task_data = response.data["tasks"][0]
        expected_fields = {
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        }
        self.assertEqual(set(task_data.keys()), expected_fields)
        self.assertEqual(task_data["assignee"]["id"], self.member.id)
        self.assertIsNone(task_data["reviewer"])
        self.assertEqual(task_data["comments_count"], 1)

    def test_member_can_view_board(self):
        self.authenticate(self.member)
        response = self.client.get(self.detail_url(self.board.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_outsider_gets_403(self):
        self.authenticate(self.outsider)
        response = self.client.get(self.detail_url(self.board.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_gets_404_for_unknown_board(self):
        self.authenticate(self.outsider)
        response = self.client.get(self.detail_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BoardDeleteTests(BoardDetailTestCase):

    def test_owner_can_delete_board(self):
        self.authenticate(self.owner)
        response = self.client.delete(self.detail_url(self.board.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Board.objects.filter(id=self.board.id).exists())

    def test_deleting_board_deletes_its_tasks(self):
        task = self.create_task("to-do", "high")
        self.authenticate(self.owner)
        self.client.delete(self.detail_url(self.board.id))
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_member_cannot_delete_board(self):
        self.authenticate(self.member)
        response = self.client.delete(self.detail_url(self.board.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Board.objects.filter(id=self.board.id).exists())

    def test_outsider_cannot_delete_board(self):
        self.authenticate(self.outsider)
        response = self.client.delete(self.detail_url(self.board.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Board.objects.filter(id=self.board.id).exists())

    def test_unknown_board_returns_404(self):
        self.authenticate(self.owner)
        response = self.client.delete(self.detail_url(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class BoardPatchTests(BoardDetailTestCase):

    def patch_board(self, data, board_id=None):
        board_id = board_id or self.board.id
        url = self.detail_url(board_id)
        return self.client.patch(url, data, format="json")

    def test_owner_can_update_title_and_members(self):
        self.authenticate(self.owner)
        response = self.patch_board({"title": "Changed",
                                     "members": [self.outsider.id]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Changed")
        member_ids = [member["id"] for member in response.data["members_data"]]
        self.assertEqual(member_ids, [self.outsider.id])

    def test_response_has_owner_data_and_members_data(self):
        self.authenticate(self.owner)
        response = self.patch_board({"title": "Changed"})
        expected_fields = {"id", "title", "owner_data", "members_data"}
        self.assertEqual(set(response.data.keys()), expected_fields)
        self.assertEqual(response.data["owner_data"]["id"], self.owner.id)

    def test_title_only_keeps_members(self):
        self.authenticate(self.owner)
        self.patch_board({"title": "Only title"})
        self.assertEqual(list(self.board.members.all()), [self.member])

    def test_member_can_update_board(self):
        self.authenticate(self.member)
        response = self.patch_board({"title": "Changed by member"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_outsider_cannot_update_board(self):
        self.authenticate(self.outsider)
        response = self.patch_board({"title": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.board.refresh_from_db()
        self.assertEqual(self.board.title, "Test Board")

    def test_unknown_board_returns_404(self):
        self.authenticate(self.owner)
        response = self.patch_board({"title": "Changed"}, board_id=9999)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unknown_member_id_returns_400(self):
        self.authenticate(self.owner)
        response = self.patch_board({"members": [9999]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_is_not_allowed(self):
        self.authenticate(self.owner)
        data = {"title": "Changed", "members": []}
        response = self.client.put(self.detail_url(self.board.id),
                                   data, format="json")
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)
