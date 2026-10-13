"""Expands the requested clouds x models x apps x trials into GitHub Actions matrices."""

from __future__ import annotations

from typing import Any

from bench import config


def plan(cfg: config.Config, clouds: str = "all", models: str = "all", apps: str = "all", trials: int = 1,
         max_parallel: int | None = None) -> dict[str, Any]:
    selected_models = config.select(cfg.models, models, "model")
    selected_apps = config.select(cfg.apps, apps, "app")
    per_cloud = []
    for cloud in config.select(cfg.clouds, clouds, "cloud"):
        cells = [
            {"model": m.id, "app": a.id, "trial": t}
            for m in selected_models
            for a in selected_apps
            for t in range(1, trials + 1)
        ]
        per_cloud.append({
            "cloud": cloud.id,
            "max_parallel": max_parallel or cfg.defaults.get("max_parallel_per_cloud", 1),
            "cells": cells,
        })
    return {
        "clouds": per_cloud,
        "cells": [{"cloud": c["cloud"], **cell} for c in per_cloud for cell in c["cells"]],
    }
