In `deployment.json`, also set `"realtime"` to `{"transport": "websocket", "url": "wss://<host>/ws"}`
or, if you implemented Server-Sent Events, `{"transport": "sse"}`.
