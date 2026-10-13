# Real-Time Collaborative App: Chat Rooms

Build a multi-user chat app where everyone in a room sees each other's messages live.

## Web UI (`GET /`)

Users pick a display name and a room (for example `/?room=general`), see the room's recent
history, and send messages that appear for everyone in the room immediately, without refreshing.

## Real-time protocol

Use **WebSockets** (preferred) or **Server-Sent Events**.

**WebSocket:** `GET /ws?room=<room>&user=<name>` upgrades to a WebSocket (`wss://` in production).

- The client sends `{"type": "message", "text": "hello"}`.
- The server broadcasts to every client connected to that room, including the sender:
  `{"type": "message", "id": "...", "room": "<room>", "user": "<name>", "text": "hello", "ts": "<ISO 8601>"}`.
- The server may send other `type`s, such as history or presence. Clients ignore unknown types.

**Server-Sent Events:** `GET /api/rooms/<room>/events` streams `text/event-stream` with one
`data: <message JSON>` event per message, in the same shape as above. Clients send with
`POST /api/rooms/<room>/messages` and the body `{"user": "<name>", "text": "hello"}`, which
responds `201` with the message.

## History API

`GET /api/rooms/<room>/messages` responds `200` with a JSON array of the room's latest messages
(up to 50, oldest first), in the same shape as above.

## Behavior

- Messages reach every client in the room within 2 seconds, including when several users post at
  the same time.
- Rooms are isolated: a message never reaches clients in other rooms.
- Messages are 1 to 1000 characters. Reject invalid ones: over HTTP with `400`; over WebSocket by
  ignoring them or replying `{"type": "error", ...}`.
