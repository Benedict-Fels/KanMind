# KanMind Backend

REST API for **KanMind**, a Kanban board application. Built with Django and Django REST Framework as part of the Developer Akademie backend course.

The API lets users register, log in, create boards, invite members, manage tasks with assignees and reviewers, and discuss tasks in comments. It is designed to work with the provided KanMind frontend (Vanilla JavaScript), which is **not** part of this repository.

---

## Tech Stack

- Python 3.12 or newer (developed with Python 3.14)
- Django 6.1
- Django REST Framework 3.18 (token authentication)
- django-cors-headers
- SQLite (development database)

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Benedict-Fels/KanMind.git
cd KanMind
```

### 2. Create and activate a virtual environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the database

The database is **not** included in the repository. Create it with:

```bash
python manage.py migrate
```

### 5. Load the demo data (recommended)

```bash
python manage.py seed_data
```

This creates three demo users, two boards, several tasks and some comments, so all features can be tried out right away. All demo users have the password `asdasdasd`:

| Email | Name | Notes |
|---|---|---|
| `kevin@kovacsi.de` | Kevin Kovacs | **Guest login** of the frontend, owner of "Website Relaunch" |
| `anna@test.de` | Anna Schmidt | Owner of "Mobile App", member of both boards |
| `max@test.de` | Max Weber | Member of "Mobile App" only |

The **guest login button** in the frontend only works after this step, because it logs in as `kevin@kovacsi.de`.

The command can be run several times without creating duplicates.

### 6. (Optional) Create an admin user

```bash
python manage.py createsuperuser
```

Use your email address as the username. The admin panel is available at `http://127.0.0.1:8000/admin/`.

### 7. Start the server

```bash
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/api/`.

---

## Connecting the Frontend

1. Download the KanMind frontend separately.
2. Open it in VS Code and start `index.html` with the **Live Server** extension (port `5500`).
3. Make sure the backend is running on `http://127.0.0.1:8000`.

CORS is configured for `http://127.0.0.1:5500` and `http://localhost:5500`. If your frontend runs on a different address, add it to `CORS_ALLOWED_ORIGINS` in `core/settings.py`.

---

## Authentication

All endpoints except registration and login require a token.

1. Get a token via `POST /api/registration/` or `POST /api/login/`.
2. Send it with every request in the `Authorization` header:

```
Authorization: Token <your-token>
```

Note: the keyword is `Token`, not `Bearer`.

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/registration/` | Create a new user and return a token |
| POST | `/api/login/` | Log in with email and password and return a token |

### Boards

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/boards/` | List all boards the user owns or is a member of |
| POST | `/api/boards/` | Create a board (the user becomes the owner) |
| GET | `/api/boards/{board_id}/` | Board details with members and tasks |
| PATCH | `/api/boards/{board_id}/` | Update title and/or members |
| DELETE | `/api/boards/{board_id}/` | Delete a board (owner only) |
| GET | `/api/email-check/?email=<email>` | Look up a user by email |

### Tasks

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/tasks/assigned-to-me/` | Tasks where the user is the assignee |
| GET | `/api/tasks/reviewing/` | Tasks where the user is the reviewer |
| POST | `/api/tasks/` | Create a task on a board |
| PATCH | `/api/tasks/{task_id}/` | Update a task |
| DELETE | `/api/tasks/{task_id}/` | Delete a task (creator or board owner only) |

### Comments

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/tasks/{task_id}/comments/` | List the comments of a task (oldest first) |
| POST | `/api/tasks/{task_id}/comments/` | Add a comment to a task |
| DELETE | `/api/tasks/{task_id}/comments/{comment_id}/` | Delete a comment (author only) |

---

## Permissions and Special Behaviour

**Registration and login**

- The email address is used as the username. Login works with email and password.
- `fullname` is split at the first space into first and last name. A single word becomes the first name.
- Passwords are checked with Django's password validators (minimum length, not too common, not only numbers, not too similar to the email).

**Board access**

- A user has access to a board if they are its **owner or a member**.
- The owner is **not** added to `members` automatically. They can add themselves, but they have full access either way.
- Members may view and edit a board. Only the owner may delete it.
- `GET /api/boards/` simply leaves out boards without access. Detail endpoints return `403` instead.
- A `PATCH` with `members` replaces the whole member list.

**Tasks**

- Only users with access to the board may create, edit or comment on its tasks.
- Assignee and reviewer must have access to the board (owner or member), otherwise the API returns `400`.
- `assignee_id` and `reviewer_id` are optional and may be `null`.
- The board of a task cannot be changed. Sending the **same** board in a `PATCH` request is allowed (the frontend always does this). Sending a **different** board returns `400`.
- A task can only be deleted by its creator or by the board owner. If the creator's account has been deleted, only the board owner can delete the task.
- `/api/tasks/assigned-to-me/` only returns tasks where the user is the **assignee**. Tasks the user reviews are returned by `/api/tasks/reviewing/`.
- Deleting a board also deletes all of its tasks and comments.

**Comments**

- Only the author of a comment can delete it, not even the board owner.
- A comment is only found under the task it belongs to. Using the comment ID with a different task ID returns `404`.

**Status codes**

- `404` is checked before `403`: a resource that does not exist always returns `404`, even if the user would not have access to it.
- `POST /api/tasks/` with an unknown board returns `404`, not `400`.
- `PUT` is not supported. Use `PATCH` for updates (`PUT` returns `405`).
- There is no `GET` for a single task, because the frontend gets all tasks through the board details.

**Response formats**

Writing and reading use different field names, as defined in the endpoint documentation:

- Users are sent as IDs (`members`, `assignee_id`, `reviewer_id`) and returned as objects (`{id, email, fullname}`).
- `GET /api/boards/{board_id}/` returns `owner_id` and `members`, while `PATCH` on the same endpoint returns `owner_data` and `members_data`.
- Comments return the author as plain text (full name), not as an object.

**Development settings**

- `DEBUG` is enabled and the `SECRET_KEY` is stored in `core/settings.py`. This setup is meant for local development only and must be changed before any deployment.

---

## Running the Tests

```bash
python manage.py test
```

Run the tests of a single app or file:

```bash
python manage.py test kanban_app
python manage.py test kanban_app.tests.test_board_detail
```

During test runs, a fast password hasher is used to keep the tests quick. The normal secure hasher is used everywhere else.

---

## Project Structure

```
KanMind/
├── core/                  # Project settings and main URL routing
├── auth_app/              # Registration and login
│   ├── api/               # Serializers, views, URLs
│   └── tests/
├── kanban_app/            # Boards, tasks, comments
│   ├── api/               # Serializers, views, URLs, permissions
│   ├── management/        # seed_data command
│   ├── migrations/
│   ├── tests/
│   ├── admin.py
│   └── models.py
├── manage.py
└── requirements.txt
```
