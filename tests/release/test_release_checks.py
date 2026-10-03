"""Release gating must use successful push runs for the exact merged commit."""

import importlib.util
import subprocess
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "release_checks", Path(__file__).resolve().parents[2] / "scripts/check_release_checks.py"
)
assert spec is not None and spec.loader is not None
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
SHA = "a" * 40


def successful_run(workflow):
    return {
        "head_sha": SHA,
        "head_branch": "master",
        "event": "push",
        "path": f".github/workflows/{workflow}",
        "status": "completed",
        "conclusion": "success",
    }


def test_requires_both_workflows_for_exact_master_commit():
    requested = []

    def read(path):
        requested.append(path)
        workflow = path.split("/workflows/", 1)[1].split("/", 1)[0]
        return {"workflow_runs": [successful_run(workflow)]}

    checks.verify_checks("IIXIXII/pymdtools", SHA, read)
    assert len(requested) == 2
    assert all(f"branch=master&event=push&head_sha={SHA}&per_page=1" in p for p in requested)


@pytest.mark.parametrize(
    "field,value",
    [
        ("head_sha", "b" * 40),
        ("head_branch", "feature"),
        ("event", "pull_request"),
        ("path", ".github/workflows/other.yml"),
        ("status", "in_progress"),
        ("conclusion", "failure"),
        ("conclusion", "cancelled"),
        ("conclusion", "skipped"),
    ],
)
def test_rejects_untrusted_or_unsuccessful_latest_run(field, value):
    run = successful_run("ci.yml")
    run[field] = value
    with pytest.raises(RuntimeError, match="has not succeeded"):
        checks.verify_checks(
            "IIXIXII/pymdtools", SHA, lambda _: {"workflow_runs": [run, successful_run("ci.yml")]}
        )


def test_missing_codeql_run_blocks_release():
    with pytest.raises(RuntimeError, match="codeql.yml: no push run"):
        checks.verify_checks(
            "IIXIXII/pymdtools",
            SHA,
            lambda path: {
                "workflow_runs": [successful_run("ci.yml")] if "/ci.yml/" in path else []
            },
        )


def test_api_failure_does_not_allow_release():
    def unavailable(_):
        raise TimeoutError("GitHub unavailable")

    with pytest.raises(TimeoutError):
        checks.verify_checks("IIXIXII/pymdtools", SHA, unavailable)


@pytest.mark.parametrize(
    "repository,sha",
    [
        ("owner/repo?other=value", SHA),
        ("owner/repo", "not-a-sha"),
    ],
)
def test_invalid_api_inputs_are_rejected(repository, sha):
    with pytest.raises(ValueError):
        checks.verify_checks(repository, sha, lambda _: pytest.fail("unexpected request"))


def test_unmerged_commit_never_reaches_github_api(monkeypatch):
    def unmerged(command, **kwargs):
        assert command == [
            "git",
            "merge-base",
            "--is-ancestor",
            "HEAD",
            "refs/remotes/origin/master",
        ]
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(checks.subprocess, "run", unmerged)
    monkeypatch.setattr(checks, "verify_checks", lambda *a: pytest.fail("unexpected request"))
    with pytest.raises(subprocess.CalledProcessError):
        checks.main()
