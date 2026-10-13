#!/usr/bin/env python3
"""Stands in for `claude -p --output-format stream-json` in smoke tests: no model calls, no cost.

A smoke-test run exercises everything around the agent (secrets, matrix, inventory and teardown
against each cloud's API, artifacts, aggregation) without building or deploying anything.
"""

import json
import sys
import uuid

MESSAGE = "Smoke test: the stub agent ran instead of Claude Code, so nothing was built or deployed."
ZERO_USAGE = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}


def flag(args: list[str], name: str, default: str) -> str:
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def emit(event: dict) -> None:
    print(json.dumps(event), flush=True)


def main() -> None:
    sys.stdin.read()
    args = sys.argv[1:]
    session = flag(args, "--resume", flag(args, "--session-id", str(uuid.uuid4())))
    model = flag(args, "--model", "stub")
    emit({"type": "system", "subtype": "init", "session_id": session, "model": model,
          "claude_code_version": "stub", "apiKeySource": "none", "tools": []})
    emit({"type": "assistant", "session_id": session, "parent_tool_use_id": None,
          "message": {"id": "msg_stub", "role": "assistant", "model": model, "usage": ZERO_USAGE,
                      "content": [{"type": "text", "text": MESSAGE}]}})
    emit({"type": "result", "subtype": "success", "is_error": False, "duration_ms": 0, "duration_api_ms": 0,
          "num_turns": 1, "result": MESSAGE, "session_id": session, "total_cost_usd": 0, "usage": ZERO_USAGE,
          "modelUsage": {}, "permission_denials": []})


if __name__ == "__main__":
    main()
