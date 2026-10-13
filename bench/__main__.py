"""Command line for the benchmark harness. Run `python -m bench --help`."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from bench import aggregate, cell, config, janitor, plan
from bench.verify import VERIFIERS
from bench.verify.browser import Browser


def write_github_output(**values: str) -> None:
    if path := os.environ.get("GITHUB_OUTPUT"):
        with open(path, "a") as f:
            for key, value in values.items():
                f.write(f"{key}={value}\n")


def cmd_plan(args: argparse.Namespace) -> None:
    result = plan.plan(config.load(), args.clouds, args.models, args.apps, args.trials, args.max_parallel)
    result["run"] = {"name": args.run_name} if args.run_name else {}
    Path(args.out).write_text(json.dumps(result, indent=2))
    write_github_output(clouds=json.dumps(result["clouds"]), cells=str(len(result["cells"])))
    print(f"{len(result['cells'])} cell(s) across {len(result['clouds'])} cloud(s):")
    for entry in result["clouds"]:
        print(f"  {entry['cloud']}: " + ", ".join(f"{c['app']}/{c['model']}#{c['trial']}" for c in entry["cells"]))


def cmd_cell(args: argparse.Namespace) -> None:
    directory = Path(args.dir)
    if args.step == "prepare":
        cell.prepare(directory, Path(args.workspace_root), args.run_id, args.cloud, args.model, args.app, args.trial)
        return
    current = cell.Cell(directory)
    {
        "build": lambda: cell.build(current),
        "deploy": lambda: cell.deploy(current),
        "inventory": lambda: cell.inventory(current),
        "verify": lambda: cell.verify(current, use_browser=not args.no_browser),
        "review": lambda: cell.review(current),
        "teardown": lambda: cell.teardown(current, keep=args.keep),
        "finalize": lambda: cell.finalize(current),
    }[args.step]()


def cmd_redact(args: argparse.Namespace) -> None:
    print(f"redacted secrets in {cell.redact(Path(args.dir))} file(s)")


def cmd_verify(args: argparse.Namespace) -> None:
    inputs = {}
    for item in args.input:
        key, _, value = item.partition("=")
        inputs[key] = value.split(",") if key == "api_keys" else value
    deployment = json.loads(Path(args.deployment).read_text()) if args.deployment else {}
    browser = None if args.no_browser else Browser.launch()
    try:
        verifier = VERIFIERS[args.app](args.url, inputs=inputs, deployment=deployment, browser=browser,
                                       require_https=not args.allow_http, min_persistence_delay=args.persistence_delay)
        report = verifier.run_all()
    finally:
        if browser:
            browser.close()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["success"] else 1)


def cmd_aggregate(args: argparse.Namespace) -> None:
    run = {"name": args.run_name, "date": args.date, "number": args.run_number, "attempt": args.run_attempt,
           "url": args.run_url}
    summary = aggregate.aggregate(Path(args.artifacts), json.loads(Path(args.plan).read_text()), Path(args.results),
                                  Path(args.readme), run)
    for group in summary["groups"]:
        print(f"{group['model']}/{group['cloud']}: {group['success']}/{group['cells']} succeeded")
    commit = summary["run"]["commit"]
    write_github_output(commit=str(commit).lower())
    if not commit:
        print("::warning::No agent could run in any cell (see each cell's deploy phase); results won't be committed")


def cmd_janitor(args: argparse.Namespace) -> None:
    report = janitor.sweep(args.cloud, args.delete, args.older_than_hours)
    print(json.dumps(report, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m bench", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan", help="expand the matrix and print GitHub Actions outputs")
    p.add_argument("--clouds", default="all")
    p.add_argument("--models", default="all")
    p.add_argument("--apps", default="all")
    p.add_argument("--trials", type=int, default=1)
    p.add_argument("--max-parallel", type=int, default=None)
    p.add_argument("--run-name", default="")
    p.add_argument("--out", default="plan.json")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("cell", help="run one step of a benchmark cell")
    p.add_argument("step", choices=["prepare", *cell_steps()])
    p.add_argument("--dir", required=True, help="cell output directory")
    p.add_argument("--workspace-root")
    p.add_argument("--run-id")
    p.add_argument("--cloud")
    p.add_argument("--model")
    p.add_argument("--app")
    p.add_argument("--trial", type=int, default=1)
    p.add_argument("--keep", action="store_true", help="teardown: keep the deployment running")
    p.add_argument("--no-browser", action="store_true", help="verify: skip checks that need Playwright")
    p.set_defaults(func=cmd_cell)

    p = sub.add_parser("redact", help="mask secret values in every file under a directory")
    p.add_argument("--dir", required=True)
    p.set_defaults(func=cmd_redact)

    p = sub.add_parser("verify", help="run an app's checks against any URL (for development)")
    p.add_argument("--app", required=True, choices=sorted(VERIFIERS))
    p.add_argument("--url", required=True)
    p.add_argument("--input", action="append", default=[], help="key=value, e.g. api_keys=key1,key2")
    p.add_argument("--deployment", help="path to a deployment.json")
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--allow-http", action="store_true")
    p.add_argument("--persistence-delay", type=float, default=60.0)
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("aggregate", help="collect cell results into results/ and update README.md")
    p.add_argument("--artifacts", required=True)
    p.add_argument("--plan", required=True)
    p.add_argument("--results", default="results")
    p.add_argument("--readme", default="README.md")
    p.add_argument("--run-name", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--run-number", type=int)
    p.add_argument("--run-attempt", type=int)
    p.add_argument("--run-url", default="")
    p.set_defaults(func=cmd_aggregate)

    p = sub.add_parser("janitor", help="list (and with --delete, remove) leftover benchmark resources")
    p.add_argument("--cloud", required=True, choices=[*sorted(cell.ADAPTERS), "github"])
    p.add_argument("--delete", action="store_true")
    p.add_argument("--older-than-hours", type=float, default=6.0)
    p.set_defaults(func=cmd_janitor)

    args = parser.parse_args(argv)
    args.func(args)


def cell_steps() -> list[str]:
    return ["build", "deploy", "inventory", "verify", "review", "teardown", "finalize"]


if __name__ == "__main__":
    main()
