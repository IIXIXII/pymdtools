"""Fail closed unless HEAD is on master and its push CI and CodeQL succeeded."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ("ci.yml", "codeql.yml")


def read_github_json(path: str) -> dict[str, Any]:
    request = urllib.request.Request(
        "https://api.github.com" + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
            "X-GitHub-Api-Version": "2026-03-10",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def verify_checks(
    repository: str,
    sha: str,
    read_json: Callable[[str], dict[str, Any]] = read_github_json,
) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("invalid GitHub repository")
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ValueError("invalid commit SHA")
    for workflow in WORKFLOWS:
        # GitHub returns newest runs first, including a rerun's current attempt.
        # Never fall back to an older successful run if a newer run failed.
        payload = read_json(
            f"/repos/{repository}/actions/workflows/{workflow}/runs"
            f"?branch=master&event=push&head_sha={sha}&per_page=1"
        )
        runs = payload.get("workflow_runs", [])
        if not runs:
            raise RuntimeError(f"{workflow}: no push run on master for {sha}")
        run = runs[0]
        expected = {
            "head_sha": sha,
            "head_branch": "master",
            "event": "push",
            "path": f".github/workflows/{workflow}",
            "status": "completed",
            "conclusion": "success",
        }
        if any(run.get(key) != value for key, value in expected.items()):
            raise RuntimeError(f"{workflow}: latest master push run has not succeeded for {sha}")


def main() -> None:
    # fetch-depth: 0 supplies origin/master; refuse tags on unmerged branches.
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", "HEAD", "refs/remotes/origin/master"],
        cwd=ROOT,
        check=True,
    )
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    verify_checks(os.environ["GITHUB_REPOSITORY"], sha)
    print(f"Master ancestry, CI and CodeQL verified for {sha}.")


if __name__ == "__main__":
    main()
