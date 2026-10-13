"""Finds and optionally deletes benchmark resources that outlived their cell (failed teardowns)."""

from __future__ import annotations

import datetime as dt
import os
from typing import Any

from bench import ROOT_PREFIX
from bench.clouds import ADAPTERS, base
from bench.clouds.github import GitHub


def sweep(cloud_id: str, delete: bool, older_than_hours: float, prefix: str = f"{ROOT_PREFIX}-") -> dict[str, Any]:
    targets: list[base.Cloud] = [GitHub(os.environ) if cloud_id == "github" else ADAPTERS[cloud_id](os.environ)]
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=older_than_hours)
    report: dict[str, Any] = {}
    for adapter in targets:
        if not adapter.configured():
            report[adapter.id] = {"skipped": "credentials not available"}
            continue
        stale = []
        for resource in adapter.list_resources():
            created = base.parse_time(resource.created_at)
            if resource.name.lower().startswith(prefix) and (created is None or created < cutoff):
                stale.append(resource.to_dict())
        entry: dict[str, Any] = {"found": [{"kind": r["kind"], "name": r["name"], "created_at": r["created_at"]} for r in stale],
                                 "errors": adapter.errors}
        if delete and stale:
            entry["outcomes"] = base.teardown(adapter, stale)
        report[adapter.id] = entry
    return report
