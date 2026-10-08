from django.urls import reverse
from rest_framework import status

from kanban_app.models import Comment
from kanban_app.tests.test_boards import BoardTestCase


class CommentTestCase(BoardTestCase):
    """A task on the shared board, with one comment by the member."""

    def setUp(self):
        super().setUp()
        self.member.first_name = "Mia"
        self.member.last_name = "Member"
        self.member.save()
        self.task = self.create_task("to-do", "high")
        self.comment = Comment.objects.create(
            task=self.task, author=self.member, content="First comment"
        )

    def list_url(self, task_id=None):
        return reverse("comment-list", kwargs={"task_id": task_id or self.task.id})


class CommentListTests(CommentTestCase):

    def test_requires_authentication(self):
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_sees_comments(self):
        self.authenticate(self.member)
        response = self.client.get(self.list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        comment_data = response.data[0]
        self.assertEqual(set(comment_data.keys()), {"id", "created_at", "author", "content"})
        self.assertEqual(comment_data["author"], "Mia Member")
        self.assertEqual(comment_data["content"], "First comment")

    def test_only_comments_of_this_task(self):
        other_task = self.create_task("done", "low")
        Comment.objects.create(task=other_task, author=self.member, content="Other")
        self.authenticate(self.member)
        response = self.client.get(self.list_url())
        self.assertEqual(len(response.data), 1)

    def test_comments_are_sorted_oldest_first(self):
        Comment.objects.create(task=self.task, author=self.owner, content="Second comment")
        self.authenticate(self.member)
        response = self.client.get(self.list_url())
        contents = [comment["content"] for comment in response.data]
        self.assertEqual(contents, ["First comment", "Second comment"])


class CommentCreateTests(CommentTestCase):

    def test_member_can_create_comment(self):
        self.authenticate(self.member)
        response = self.client.post(self.list_url(), {"content": "Hello"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"], "Mia Member")
        self.assertEqual(response.data["content"], "Hello")

    def test_comment_is_attached_to_task_and_author(self):
        self.authenticate(self.member)
        response = self.client.post(self.list_url(), {"content": "Hello"}, format="json")
        comment = Comment.objects.get(id=response.data["id"])
        self.assertEqual(comment.task, self.task)
        self.assertEqual(comment.author, self.member)

    def test_empty_content_returns_400(self):
        self.authenticate(self.member)
        response = self.client.post(self.list_url(), {"content": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("content", response.data)
