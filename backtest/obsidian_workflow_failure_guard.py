"""Offline, redacted OBSIDIAN workflow failure triage (research only).

No API calls, credentials, scheduling changes, or order functionality.
"""
from pathlib import Path
import json
import re
import sys

MAIN_WORKFLOWS = (
    ".github/workflows/evidence-archive.yml",
    ".github/workflows/daily-adaptive.yml",
    ".github/workflows/multiyear-research.yml",
)
PAPER_DIAGNOSTIC = ".github/workflows/obsidian-alpaca-connection-check.yml"


def classify_log(log: str) -> str:
    """Return a bounded reason code, never raw log lines or secret values."""
    if re.search(r"data\.alpaca\.markets[^\n]{0,100}HTTP 401", log, re.I):
        return "ALPACA_MARKET_DATA_AUTH_401"
    if re.search(r"data\.alpaca\.markets[^\n]{0,100}HTTP 403", log, re.I):
        return "ALPACA_MARKET_DATA_ACCESS_403"
    if re.search(r"(?:FAILED \(failures=|AssertionError:|^FAIL: test_)", log, re.M):
        return "OFFLINE_TEST_ASSERTION"
    if "Path Validation Error" in log and "Process completed with exit code 1" not in log:
        return "CACHE_PATH_WARNING_ONLY"
    if "Process completed with exit code" in log:
        return "UNCLASSIFIED_FAILED_STEP"
    return "NO_VERIFIED_FAILURE"


def credential_contract(root: Path) -> dict:
    """Compare *names* of workflow secret references; never resolve secrets."""
    files = {name: (root / name).read_text(encoding="utf-8")
             for name in (*MAIN_WORKFLOWS, PAPER_DIAGNOSTIC)}
    main = all(
        "${{ secrets.ALPACA_API_KEY }}" in files[name]
        and "${{ secrets.ALPACA_SECRET_KEY }}" in files[name]
        for name in MAIN_WORKFLOWS
    )
    paper = (
        "${{ secrets.OBSIDIAN_PAPER_API_KEY_ID }}" in files[PAPER_DIAGNOSTIC]
        and "${{ secrets.OBSIDIAN_PAPER_SECRET_KEY }}" in files[PAPER_DIAGNOSTIC]
    )
    return {
        "status": "SEPARATE_CREDENTIAL_FAMILIES" if main and paper else "WORKFLOW_AUTH_CONTRACT_CHANGED",
        "main_uses_legacy_alpaca_secret_names": main,
        "research_diagnostic_uses_paper_secret_names": paper,
        "paper_diagnostic_proves_main_auth": False,
        "secret_values_read": False,
    }


def triage(root: Path, log_text: str) -> dict:
    return {"mode": "RESEARCH_ONLY_NOT_AN_ORDER",
            "credential_contract": credential_contract(root),
            "failure_code": classify_log(log_text)}


if __name__ == "__main__":
    # Read from stdin only; no network or credential access.
    print(json.dumps(triage(Path(__file__).resolve().parents[1], sys.stdin.read()), sort_keys=True))
