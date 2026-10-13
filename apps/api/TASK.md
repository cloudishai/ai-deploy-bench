# API / Backend Service: Notes API

Build a JSON REST API for storing notes, meant to be consumed by other programs. No UI is
required.

## Authentication

- Every `/v1/*` request carries an API key in the `X-API-Key` header. A missing or unknown key
  gets `401` with `{"error": "..."}`.
- Valid keys come from the `API_KEYS` environment variable, a comma-separated list such as
  `API_KEYS=key-one,key-two`.
- Notes belong to the key that created them. Other keys can't read, list, update or delete them
  (respond `404`).

## Rate limiting

- At most **60 requests per minute per API key** across `/v1/*`. Further requests get `429` with
  a `Retry-After` header (in seconds) and `{"error": "..."}`.
- Limits are tracked per key: one key reaching its limit doesn't affect other keys.

## Endpoints

| Method and path               | Body                                      | Success                                          | Errors                                   |
|-------------------------------|-------------------------------------------|--------------------------------------------------|------------------------------------------|
| `GET /health` (no auth)       |                                           | `200` with `{"status": "ok"}`                    |                                          |
| `GET /openapi.json` (no auth) |                                           | `200` with an OpenAPI 3 document of every endpoint |                                        |
| `GET /docs` (no auth)         |                                           | `200` with human-readable API docs (HTML)        |                                          |
| `POST /v1/notes`              | `{"title", "content", "tags"?: [string]}` | `201` with the note                              | `400` missing or empty `title`, wrong types |
| `GET /v1/notes`               | optional query `tag` filter               | `200` with `{"data": [notes...]}`, newest first  |                                          |
| `GET /v1/notes/{id}`          |                                           | `200` with the note                              | `404`                                    |
| `PATCH /v1/notes/{id}`        | any of `title`, `content`, `tags`         | `200` with the updated note                      | `400`, `404`                             |
| `DELETE /v1/notes/{id}`       |                                           | `204`                                            | `404`                                    |

A note is
`{"id": "...", "title": "...", "content": "...", "tags": ["..."], "created_at": "<ISO 8601>", "updated_at": "<ISO 8601>"}`.

## Data

Store notes in a database that survives restarts and redeploys, not in memory.
