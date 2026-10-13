"""Scrubs secrets from files before they leave the runner as artifacts or committed results.

GitHub masks secrets in job logs, but not in files, and transcripts can echo whatever the agent
printed. Besides the known secret values, credential-shaped strings are masked too: passwords in
URLs and well-known token formats, which covers credentials the agent obtained itself (database
URLs, keys it minted).
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import quote

MASK = "[REDACTED]"
MIN_LENGTH = 8
SKIPPED_SUFFIXES = (".gz", ".tgz", ".zip")  # archives are built from already-redacted files

URL_PASSWORD = r"(\b[A-Za-z][A-Za-z0-9+.-]*://[^\s:/@'\"]+:)([^\s@/'\"]{3,})(@)"
TOKEN_FORMATS = (
    r"\bsk-ant-[A-Za-z0-9_-]{20,}",  # Anthropic
    r"\bdop_v1_[a-f0-9]{40,}",  # DigitalOcean
    r"\brnd_[A-Za-z0-9]{20,}",  # Render
    r"\bvcp_[A-Za-z0-9]{20,}",  # Vercel
    r"\bcld_[A-Za-z0-9_-]{16,}",  # Cloudish
    r"\bgh[pousr]_[A-Za-z0-9]{30,}",  # GitHub
    r"\bgithub_pat_[A-Za-z0-9_]{40,}",
    r"\bAKIA[0-9A-Z]{16}\b",  # AWS access key id
)
_URL_TEXT = re.compile(URL_PASSWORD)
_TOKENS_TEXT = re.compile("|".join(TOKEN_FORMATS))
_URL_BYTES = re.compile(URL_PASSWORD.encode())
_TOKENS_BYTES = re.compile("|".join(TOKEN_FORMATS).encode())


def secret_values(env: Mapping[str, str], names: Iterable[str], extra: Iterable[str] = ()) -> list[str]:
    values = set()
    for value in [env.get(name) or "" for name in names] + list(extra):
        if len(value) >= MIN_LENGTH:
            values.add(value)
            values.add(quote(value, safe=""))
    # Longest first, so a secret that contains another is masked whole.
    return sorted(values, key=len, reverse=True)


def redact_text(text: str, secrets: Iterable[str]) -> str:
    for secret in secrets:
        text = text.replace(secret, MASK)
    text = _URL_TEXT.sub(lambda m: m.group(1) + MASK + m.group(3), text)
    return _TOKENS_TEXT.sub(MASK, text)


def redact_bytes(data: bytes, secrets: list[bytes]) -> bytes:
    for secret in secrets:
        data = data.replace(secret, MASK.encode())
    data = _URL_BYTES.sub(lambda m: m.group(1) + MASK.encode() + m.group(3), data)
    return _TOKENS_BYTES.sub(MASK.encode(), data)


def redact_file(path: Path, secrets: list[bytes]) -> bool:
    """Rewrites `path` line by line at the byte level, so any size and encoding works."""
    changed = False
    with path.open("rb") as source, tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as target:
        for line in source:
            cleaned = redact_bytes(line, secrets)
            changed = changed or cleaned != line
            target.write(cleaned)
    if changed:
        os.replace(target.name, path)
    else:
        os.unlink(target.name)
    return changed


def redact_tree(root: Path, secrets: list[str]) -> int:
    """Masks secrets in every file under `root`; returns how many files changed."""
    encoded = [s.encode() for s in secrets]
    changed = 0
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink() and not path.name.endswith(SKIPPED_SUFFIXES):
            changed += redact_file(path, encoded)
    return changed
