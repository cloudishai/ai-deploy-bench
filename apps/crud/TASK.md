# Database-Backed CRUD App: Multi-user Todo List

Build a multi-user todo list web app with accounts. Users sign up, log in, and manage their own
todos.

## Web UI

`GET /` serves the web app (HTML). From the browser a user can sign up, log in, log out, and
create, list, rename, complete or uncomplete, and delete their todos.

## JSON API

Request and response bodies are JSON. Authenticated endpoints accept
`Authorization: Bearer <token>`, where the token comes from signup or login. The web UI may also
use cookies.

| Method and path          | Body                            | Success                                        | Errors                                                                 |
|--------------------------|---------------------------------|------------------------------------------------|------------------------------------------------------------------------|
| `POST /api/auth/signup`  | `{"email", "password"}`         | `201` with `{"token": "..."}`                  | `400` invalid email or password shorter than 8 characters; `409` email already registered |
| `POST /api/auth/login`   | `{"email", "password"}`         | `200` with `{"token": "..."}`                  | `401` wrong credentials                                                |
| `GET /api/todos`         |                                 | `200` with an array of the caller's todos, oldest first | `401` not authenticated                                      |
| `POST /api/todos`        | `{"title"}`                     | `201` with the created todo                    | `400` empty title; `401`                                               |
| `PATCH /api/todos/{id}`  | `{"title"?, "completed"?}`      | `200` with the updated todo                    | `404` missing or owned by another user; `401`                          |
| `DELETE /api/todos/{id}` |                                 | `204`                                          | `404` missing or owned by another user; `401`                          |

A todo is `{"id": <string or number>, "title": "...", "completed": false, "created_at": "<ISO 8601>"}`.

## Data and security

- Store users and todos in a real database that survives restarts and redeploys, for example a
  managed PostgreSQL, or SQLite on a persistent volume. In-memory or ephemeral-disk storage is not
  acceptable.
- Hash passwords with a slow password hash (bcrypt, scrypt or argon2) and never return hashes.
- Users can only see and modify their own todos.
