from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from kanban_app.models import Board, Task

BOARDS_URL = "/api/boards/"


def create_user(email):
    return User.objects.create_user(username=email, email=email, password="testpass123")


class BoardTestCase(APITestCase):
    """Shared setup: one board with an owner, one member and one outsider."""

    def setUp(self):
        self.owner = create_user("owner@test.de")
        self.member = create_user("member@test.de")
        self.outsider = create_user("outsider@test.de")
        self.board = Board.objects.create(title="Test Board", owner=self.owner)
        self.board.members.add(self.member)

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def create_task(self, task_status, priority):
        return Task.objects.create(
            board=self.board,
            title="Test Task",
            status=task_status,
            priority=priority,
            created_by=self.owner,
        )


class BoardListTests(BoardTestCase):

    def test_requires_authentication(self):
        response = self.client.get(BOARDS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_sees_own_board(self):
        self.authenticate(self.owner)
        response = self.client.get(BOARDS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.board.id)

    def test_member_sees_board(self):
        self.authenticate(self.member)
        response = self.client.get(BOARDS_URL)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.board.id)

    def test_outsider_does_not_see_board(self):
        self.authenticate(self.outsider)
        response = self.client.get(BOARDS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_owner_who_is_also_member_gets_board_once(self):
        self.board.members.add(self.owner)
        self.authenticate(self.owner)
        response = self.client.get(BOARDS_URL)
        self.assertEqual(len(response.data), 1)

    def test_counters_are_correct(self):
        self.create_task("to-do", "high")
        self.create_task("to-do", "low")
        self.create_task("done", "high")
        self.authenticate(self.owner)
        board_data = self.client.get(BOARDS_URL).data[0]
        self.assertEqual(board_data["member_count"], 1)
        self.assertEqual(board_data["ticket_count"], 3)
        self.assertEqual(board_data["tasks_to_do_count"], 2)
        self.assertEqual(board_data["tasks_high_prio_count"], 2)
        self.assertEqual(board_data["owner_id"], self.owner.id)

    def test_response_contains_exactly_the_documented_fields(self):
        self.authenticate(self.owner)
        board_data = self.client.get(BOARDS_URL).data[0]
        expected_fields = {
            "id",
            "title",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        }
        self.assertEqual(set(board_data.keys()), expected_fields)


class BoardCreateTests(BoardTestCase):

    def test_requires_authentication(self):
        data = {"title": "New Board", "members": []}
        response = self.client.post(BOARDS_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Board.objects.filter(title="New Board").exists())

    def test_create_board_sets_logged_in_user_as_owner(self):
        self.authenticate(self.owner)
        data = {"title": "New Board", "members": [self.member.id]}
        response = self.client.post(BOARDS_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Board")
        self.assertEqual(response.data["owner_id"], self.owner.id)
        self.assertTrue(Board.objects.filter(title="New Board", owner=self.owner).exists())

    def test_owner_is_not_added_as_member_automatically(self):
        self.authenticate(self.owner)
        data = {"title": "New Board", "members": [self.member.id, self.outsider.id]}
        response = self.client.post(BOARDS_URL, data, format="json")
        self.assertEqual(response.data["member_count"], 2)
        board = Board.objects.get(id=response.data["id"])
        self.assertNotIn(self.owner, board.members.all())

    def test_unknown_member_id_returns_400(self):
        self.authenticate(self.owner)
        data = {"title": "New Board", "members": [9999]}
        response = self.client.post(BOARDS_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("members", response.data)

    def test_missing_title_returns_400(self):
        self.authenticate(self.owner)
        data = {"members": [self.member.id]}
        response = self.client.post(BOARDS_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)
