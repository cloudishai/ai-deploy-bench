import re

from bench import cell, config
from bench.clouds import base
from bench.clouds.base import Resource

# DigitalOcean app names are the strictest: ^[a-z][a-z0-9-]{0,30}[a-z0-9]$ (max 32 chars).
DO_NAME = re.compile(r"^[a-z][a-z0-9-]{0,30}[a-z0-9]$")


def test_prefixes_are_unique_and_leave_room_for_suffixes():
    cfg = config.load()
    prefixes = {
        cell.make_prefix(run, c.id, m.id, a.id, trial)
        for run in ("100-1", "100-2", "101-1")
        for c in cfg.clouds
        for m in cfg.models
        for a in cfg.apps
        for trial in (1, 2)
    }
    assert len(prefixes) == 3 * len(cfg.clouds) * len(cfg.models) * len(cfg.apps) * 2
    for prefix in prefixes:
        assert DO_NAME.match(prefix + "-web-db"), prefix


def test_build_env_has_no_cloud_or_harness_credentials(monkeypatch):
    cfg = config.load()
    for name, value in {"ANTHROPIC_API_KEY": "sk", "VERCEL_TOKEN": "v", "RENDER_API_KEY": "r", "GH_TOKEN": "g",
                        "GH_OWNER": "o", "GITHUB_TOKEN": "harness", "PATH": "/usr/bin"}.items():
        monkeypatch.setenv(name, value)
    env = cell.agent_env(cfg, cloud=None)
    assert env["ANTHROPIC_API_KEY"] == "sk" and env["PATH"] == "/usr/bin"
    assert not {"VERCEL_TOKEN", "RENDER_API_KEY", "GH_TOKEN", "GH_OWNER", "GITHUB_TOKEN"} & env.keys()


def test_deploy_env_has_only_the_target_clouds_credentials(monkeypatch):
    cfg = config.load()
    monkeypatch.setenv("VERCEL_TOKEN", "v")
    monkeypatch.setenv("VERCEL_TEAM_ID", "")
    monkeypatch.setenv("RENDER_API_KEY", "r")
    monkeypatch.setenv("GITHUB_TOKEN", "harness")
    monkeypatch.setenv("GH_TOKEN", "g")
    monkeypatch.delenv("GH_OWNER", raising=False)
    env = cell.agent_env(cfg, cfg.cloud("vercel"), extra={"BENCH_API_KEYS": "a,b"})
    assert env["VERCEL_TOKEN"] == "v" and env["BENCH_API_KEYS"] == "a,b"
    # Empty optional variables, other clouds' secrets, harness tokens and half-configured GitHub access are dropped.
    assert not {"VERCEL_TEAM_ID", "RENDER_API_KEY", "GITHUB_TOKEN", "GH_TOKEN"} & env.keys()
    monkeypatch.setenv("GH_OWNER", "bench-org")
    env = cell.agent_env(cfg, cfg.cloud("vercel"))
    assert env["GH_TOKEN"] == "g" and env["GH_OWNER"] == "bench-org"


def test_teardown_spares_declared_resources_that_predate_the_cell(tmp_path, monkeypatch):
    current = cell.prepare(tmp_path / "cell", tmp_path / "work", "9-1", "digitalocean", "opus-5-5", "api", 1)
    current.write("deploy/phase.json", {"name": "deploy", "status": "completed", "started_at": "2026-10-12T10:00:00+00:00"})
    current.write("deployment.json", {"url": "https://x", "resources": [{"name": "shared-registry"}, {"name": "my-db"}]})
    deleted = []

    class Fake(base.Cloud):
        id = "fake"

        def configured(self):
            return True

        def list_resources(self):
            gone = set(deleted)
            return [r for r in (
                Resource("registry", "r1", "shared-registry", created_at="2026-01-01T00:00:00Z"),
                Resource("database", "d1", "my-db", created_at="2026-10-12T10:07:00Z"),
                Resource("app", "a1", current.prefix + "-web", created_at="2026-10-12T10:05:00Z"),
            ) if r.id not in gone]

        def delete(self, resource):
            deleted.append(resource.id)

    monkeypatch.setattr(cell, "adapters", lambda _: [("cloud", Fake({}))])
    report = cell.teardown(current)
    assert sorted(deleted) == ["a1", "d1"]
    assert report["cloud"]["kept"] == ["shared-registry"]
    assert report["cloud"]["leftovers"] == []


def test_credentials_the_agent_saved_are_inventoried_and_hidden(tmp_path, monkeypatch):
    monkeypatch.setenv("CLOUDISH_API_KEY", "cld_provided_0123456789")
    current = cell.prepare(tmp_path / "cell", tmp_path / "work", "9-2", "cloudish", "opus-5-5", "static", 1)
    (current.workspace / ".env").write_text("CLOUDISH_API_KEY=cld_minted_by_agent_0123\nOTHER=value-not-a-credential\n")
    assert cell.workspace_credentials(current) == [{"CLOUDISH_API_KEY": "cld_minted_by_agent_0123"}]
    roles = [(role, adapter.env.get("CLOUDISH_API_KEY")) for role, adapter in cell.adapters(current)]
    assert ("cloud", "cld_provided_0123456789") in roles and ("cloud", "cld_minted_by_agent_0123") in roles
    assert "cld_minted_by_agent_0123" in cell.secrets_to_hide(current.config, current)
