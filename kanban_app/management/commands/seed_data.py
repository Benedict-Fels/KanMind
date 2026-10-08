"""Management command that fills the database with demo data."""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from kanban_app.models import Board, Comment, Task

PASSWORD = "asdasdasd"

# (email, first_name, last_name)
USERS = [
    ("kevin@kovacsi.de", "Kevin", "Kovacs"),
    ("anna@test.de", "Anna", "Schmidt"),
    ("max@test.de", "Max", "Weber"),
]

# board title -> (owner, members)
BOARDS = {
    "Website Relaunch": ("kevin@kovacsi.de",
                         ["kevin@kovacsi.de", "anna@test.de"]),
    "Mobile App": ("anna@test.de", ["anna@test.de", "max@test.de"]),
}

# board title -> [(title, status, priority, assignee, reviewer, due_in_days)]
TASKS = {
    "Website Relaunch": [
        ("Design homepage", "to-do", "high",
         "anna@test.de", "kevin@kovacsi.de", 7),
        ("Set up hosting", "in-progress",
         "medium", "kevin@kovacsi.de", None, 3),
        ("Write imprint", "review", "low", None, None, None),
        ("Collect content", "done", "medium", "anna@test.de", None, -2),
    ],
    "Mobile App": [
        ("Create wireframes", "to-do", "high",
         "max@test.de", "anna@test.de", 10),
        ("Choose framework", "done", "low", "anna@test.de", None, None),
    ],
}

# task title -> [(author, content)]
COMMENTS = {
    "Design homepage": [
        ("anna@test.de", "First draft is in Figma."),
        ("kevin@kovacsi.de", "Looks good, please make the header smaller."),
    ],
}


class Command(BaseCommand):
    """Create demo users, boards, tasks and comments."""

    help = (
        "Create demo users, boards, tasks and comments "
        "for local development."
    )

    def handle(self, *args, **options):
        """Create all demo data. Running it twice creates no duplicates."""
        users = self.create_users()
        for board_title, (owner_email, member_emails) in BOARDS.items():
            board = self.create_board(
                board_title, owner_email, member_emails, users)
            self.create_tasks(board, TASKS.get(board_title, []), users)
        self.stdout.write(self.style.SUCCESS("Demo data created."))

    def create_users(self):
        """Create the demo users if missing and return them by email."""
        users = {}
        for email, first_name, last_name in USERS:
            user = User.objects.filter(username=email).first()
            if user is None:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=PASSWORD,
                    first_name=first_name,
                    last_name=last_name,
                )
            users[email] = user
        return users

    def create_board(self, title, owner_email, member_emails, users):
        """Create the board if missing and set its members."""
        board, _ = Board.objects.get_or_create(
            title=title, owner=users[owner_email])
        board.members.set([users[email] for email in member_emails])
        return board

    def create_tasks(self, board, task_data, users):
        """Create the demo tasks and comments of a board once."""
        if board.tasks.exists():
            return
        for (title, status, priority, assignee,
             reviewer, due_in_days) in task_data:
            due_date = None
            if due_in_days is not None:
                due_date = date.today() + timedelta(days=due_in_days)
            task = Task.objects.create(
                board=board,
                title=title,
                description=f"Demo task: {title}",
                status=status,
                priority=priority,
                assignee=users.get(assignee),
                reviewer=users.get(reviewer),
                due_date=due_date,
                created_by=board.owner,
            )
            for author_email, content in COMMENTS.get(title, []):
                Comment.objects.create(
                    task=task, author=users[author_email], content=content)
