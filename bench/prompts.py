"""Renders the build and deploy prompts. Only the cloud, credentials and prefix vary between cells."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from bench.config import App, Cloud

TEMPLATES = Path(__file__).parent / "templates"

FRESH_SESSION_PREAMBLE = """\
The build step ended before a session could be created, so this is a new session. The current
directory holds whatever was built so far. First finish building the application in `TASK.md`
(copied at the end), then deploy it.

"""

GITHUB_CREDENTIAL = (
    "- `GH_TOKEN`: a GitHub token that can create repositories and push container images under the "
    "`{owner}` account, in case {cloud_name} deploys from a Git repository or a container registry. "
    "`GH_OWNER` holds the account name. Name repositories and images with the same prefix."
)


def github_owner(env: Mapping[str, str]) -> str | None:
    return env.get("GH_OWNER") if env.get("GH_TOKEN") and env.get("GH_OWNER") else None


def credential_lines(cloud: Cloud, env: Mapping[str, str]) -> str:
    lines = [f"- `{c.env}`: {c.description}" for c in cloud.credentials if not c.optional or env.get(c.env)]
    if owner := github_owner(env):
        lines.append(GITHUB_CREDENTIAL.format(owner=owner, cloud_name=cloud.name))
    return "\n".join(lines)


def build_prompt(cloud: Cloud, app: App) -> str:
    template = (TEMPLATES / "build.md").read_text()
    return template.format(cloud_name=cloud.name, cloud_url=cloud.url, task=app.task.strip())


def deploy_prompt(cloud: Cloud, app: App, prefix: str, env: Mapping[str, str], fresh_session: bool = False) -> str:
    template = (TEMPLATES / "deploy.md").read_text()
    notes = f"- {' '.join(app.deploy_notes.split())}\n" if app.deploy_notes else ""
    prompt = template.format(
        preamble=FRESH_SESSION_PREAMBLE if fresh_session else "",
        cloud_name=cloud.name,
        cloud_url=cloud.url,
        credentials=credential_lines(cloud, env),
        prefix=prefix,
        app_notes=notes,
    )
    if fresh_session:
        prompt += "\n---\n\n" + app.task.strip() + "\n"
    return prompt
