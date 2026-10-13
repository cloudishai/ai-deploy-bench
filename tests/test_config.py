"""Keeps benchmark.yaml consistent with docs/*.md and with the code that serves each entry."""

import re
from urllib.parse import urlsplit

from bench import config
from bench.clouds import ADAPTERS
from bench.clouds.base import PRICING_DIR
from bench.verify import VERIFIERS

DOCS = config.ROOT / "docs"


def bullet_items(path):
    return [m.group(1).strip() for m in re.finditer(r"^- (.+)$", path.read_text(), re.M)]


def bare_domain(value: str) -> str:
    host = urlsplit(value if "://" in value else "https://" + value).hostname or ""
    return host.removeprefix("www.")


def test_clouds_match_docs():
    cfg = config.load()
    assert sorted(bare_domain(d) for d in bullet_items(DOCS / "clouds.md")) == sorted(bare_domain(c.url) for c in cfg.clouds)


def test_models_match_docs():
    cfg = config.load()
    assert bullet_items(DOCS / "models.md") == [m.name for m in cfg.models]


def test_apps_match_docs():
    cfg = config.load()
    headings = re.findall(r"^## \d+\. (.+)$", (DOCS / "apps.md").read_text(), re.M)
    assert headings == [a.name for a in cfg.apps]


def test_every_entry_is_implemented():
    cfg = config.load()
    for app in cfg.apps:
        assert (app.dir / "TASK.md").exists(), app.id
        assert app.id in VERIFIERS, app.id
    for cloud in cfg.clouds:
        assert cloud.id in ADAPTERS, cloud.id
        assert (PRICING_DIR / f"{cloud.id}.yaml").exists(), cloud.id
        adapter_credentials = set(ADAPTERS[cloud.id].credentials)
        assert adapter_credentials <= {c.env for c in cloud.credentials if not c.optional}, cloud.id
    for model in cfg.models:
        assert model.model in cfg.model_prices, model.id
