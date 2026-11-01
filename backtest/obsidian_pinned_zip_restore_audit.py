"""Offline, read-only verification of frozen OBSIDIAN GitHub Actions ZIP receipts.

RESEARCH_ONLY_NOT_AN_ORDER. Requires separately downloaded original ZIP bytes;
no API calls, market orders, credentials, performance scoring or durable backup.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

# Frozen Oct 30 artifact IDs and GitHub artifact ZIP SHA256 receipts.
PINNED = {
    13006897253: ("ba983a61e2503b44e2e5501519ff3ee4a85be41a3312c2d1948a18175570cbc4", ("manifest.json", "universe.jsonl")),
    13018333034: ("956448af203a64b16551f2921cac85997f53dbbceeaf725b8b816a2c5173c8bc", ("ledger.json", "summary.json")),
    12985950392: ("4baaa22217c1cdf157fc102e1aaed3238513bb94ba2c61ff3d1c72a590f18eb1", ("attention.json", "manifest.json", "separate_async_retained_venue_coverage_audit.json", "universe.jsonl")),
    12995764777: ("f04e948242abbc6c6f87e36149bdd327bca3b3dadb2032be685696df95a43a96", ("attention.json", "manifest.json", "separate_async_retained_venue_coverage_audit.json", "universe.jsonl")),
    13006191628: ("059ae485699813b940a18a3d124cd7e26ec9a817c179ce52d487b05c8c4d00b6", ("manifest.json", "rescue.jsonl")),
    13008429628: ("a305c830924abda6da875efaa918db6d34730298dda7394d7033df3735a8eead", ("attention.json", "manifest.json", "universe.jsonl")),
    13010065001: ("f401405bea705ea0c5cb461e168385c07206a8429f1874acde69ed02e5931359", ("obsidian-independent-source-41122875006.json",)),
}

# Exact sorted roster identity from original October 30 monitor artifact 13010065001.
# The 136 retained names intentionally include nine off-universe references.
FROZEN_MONITOR_ROSTER_SHA256 = "6fd523c5d8142724a799527b28dede2e260f1a6230ea89832e5655ad1e8615c1"
CAPTURE_COHORT_IDS = (13006897253, 12985950392, 12995764777, 13006191628, 13008429628)


def cohort_identity_report(captures, ledger_symbols, monitor_symbols,
                           expected_roster_sha=FROZEN_MONITOR_ROSTER_SHA256):
    """Verify exact cross-capture membership, without treating monitors as predictions.

    A fixed denominator alone cannot detect a dropped symbol replaced by
    another symbol. The monitor is a separately retained watchlist: its nine
    off-universe references must NOT be silently inserted into the 8,510
    original cohort or scored as independent issuer/day predictions.
    """
    require(isinstance(captures, dict) and set(captures) == set(CAPTURE_COHORT_IDS),
            "CAPTURE_COHORT_SET_INCOMPLETE")
    base = set(captures[13006897253])
    require(len(base) == 8510 and len(captures[13006897253]) == 8510,
            "PRECLOSE_COHORT_IDENTITY_INVALID")
    for artifact_id in CAPTURE_COHORT_IDS:
        names = captures[artifact_id]
        require(len(names) == 8510 and len(set(names)) == 8510 and set(names) == base,
                "CROSS_ARTIFACT_COHORT_IDENTITY_DRIFT")
    require(len(ledger_symbols) == 8510 and len(set(ledger_symbols)) == 8510
            and set(ledger_symbols) == base, "MATURITY_LEDGER_COHORT_IDENTITY_DRIFT")
    require(len(monitor_symbols) == 136 and len(set(monitor_symbols)) == 136,
            "FROZEN_MONITOR_ROSTER_COUNT_OR_DUPLICATES")
    roster_sha = sha256(("\\n".join(sorted(monitor_symbols)) + "\\n").encode("utf-8"))
    require(roster_sha == expected_roster_sha, "FROZEN_136_ROSTER_SHA256_MISMATCH")
    off_universe = sorted(set(monitor_symbols) - base)
    return {
        "capture_and_maturity_symbol_sets_identical": True,
        "frozen_monitor_roster_sha256": roster_sha,
        "monitor_on_original_universe_count": 136 - len(off_universe),
        "monitor_off_original_universe_count": len(off_universe),
        "monitor_off_original_universe_symbols": off_universe,
        "off_universe_names_added_to_frozen_cohort": False,
        "duplicate_issuer_day_predictions_created": False,
    }


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def inspect_zip(path, expected_sha, expected_members):
    """Verify original ZIP bytes, CRC and exact members; never extract files."""
    raw = Path(path).read_bytes()
    require(sha256(raw) == expected_sha, "PINNED_ZIP_SHA256_MISMATCH")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "DUPLICATE_ZIP_MEMBER")
        require(set(names) == set(expected_members), "ZIP_MEMBER_SET_MISMATCH")
        require(all(not name.startswith("/") and ".." not in Path(name).parts for name in names),
                "UNSAFE_ZIP_MEMBER_PATH")
        require(archive.testzip() is None, "ZIP_CRC_FAILURE")
        contents = {name: archive.read(name) for name in names}
    return contents


def jsonl_symbols(raw):
    rows = [json.loads(line) for line in raw.splitlines() if line]
    symbols = [row.get("asset", {}).get("symbol") or row.get("ticker") or row.get("symbol")
               for row in rows]
    require(all(isinstance(symbol, str) and symbol for symbol in symbols), "MISSING_SYMBOL")
    require(len(set(symbols)) == len(symbols), "DUPLICATE_SYMBOL")
    return symbols


def audit_directory(directory):
    """Validate all seven pinned receipts and original cross-artifact links."""
    restored = {}
    captured_cohorts = {}
    rows = []
    for artifact_id, (expected_sha, members) in PINNED.items():
        path = Path(directory) / f"github-actions-artifact-{artifact_id}.zip"
        contents = inspect_zip(path, expected_sha, members)
        restored[artifact_id] = contents
        row = {"artifact_id": artifact_id, "zip_sha256": expected_sha,
               "zip_sha256_verified": True, "zip_crc_verified": True,
               "exact_members_verified": True}
        if "manifest.json" in contents:
            manifest = json.loads(contents["manifest.json"])
            if "universe.jsonl" in contents:
                symbols = jsonl_symbols(contents["universe.jsonl"])
                captured_cohorts[artifact_id] = symbols
                require(len(symbols) == 8510 == manifest["universe_count"], "UNIVERSE_DENOMINATOR_MISMATCH")
                require(sha256(contents["universe.jsonl"]) == manifest["universe_sha256"],
                        "UNIVERSE_INNER_SHA256_MISMATCH")
                require(sum(manifest["status_counts"].values()) == 8510,
                        "STATUS_PARTITION_MISMATCH")
                if "attention.json" in contents:
                    require(sha256(contents["attention.json"]) == manifest["attention_sha256"],
                            "ATTENTION_INNER_SHA256_MISMATCH")
                row["unique_symbols"] = len(symbols)
            if "rescue.jsonl" in contents:
                symbols = jsonl_symbols(contents["rescue.jsonl"])
                captured_cohorts[artifact_id] = symbols
                require(len(symbols) == 8510 == manifest["original_universe_count"],
                        "DELAYED_SIP_DENOMINATOR_MISMATCH")
                require(sha256(contents["rescue.jsonl"]) == manifest["rescue_rows_sha256"],
                        "DELAYED_SIP_INNER_SHA256_MISMATCH")
                require(sum(manifest["status_counts"].values()) == 8510,
                        "DELAYED_SIP_PARTITION_MISMATCH")
                row["unique_symbols"] = len(symbols)
        rows.append(row)

    preclose = restored[13006897253]
    intraday = restored[12995764777]
    delayed = json.loads(restored[13006191628]["manifest.json"])
    require(delayed["original_manifest_sha256"] == sha256(intraday["manifest.json"]),
            "DELAYED_SIP_SOURCE_MANIFEST_LINK_MISMATCH")
    require(delayed["original_universe_sha256"] == json.loads(intraday["manifest.json"])["universe_sha256"],
            "DELAYED_SIP_SOURCE_UNIVERSE_LINK_MISMATCH")
    summary = json.loads(restored[13018333034]["summary.json"])
    ledger_raw = restored[13018333034]["ledger.json"]
    ledger = json.loads(ledger_raw)
    require(sha256(ledger_raw) == summary["maturity_ledger_sha256"], "MATURITY_LEDGER_SHA256_MISMATCH")
    require(summary["original_zip_sha256"] == PINNED[13006897253][0],
            "MATURITY_SOURCE_ZIP_LINK_MISMATCH")
    require(summary["original_universe_sha256"] == json.loads(preclose["manifest.json"])["universe_sha256"],
            "MATURITY_SOURCE_UNIVERSE_LINK_MISMATCH")
    require(len(ledger["rows"]) == 8510 and len({r["ticker"] for r in ledger["rows"]}) == 8510,
            "MATURITY_UNIQUE_ISSUER_DENOMINATOR_MISMATCH")
    require(sum(len(r["horizons"]) for r in ledger["rows"]) == 34040,
            "MATURITY_HORIZON_DENOMINATOR_MISMATCH")
    require(all([h["horizon"] for h in r["horizons"]] == [0, 1, 2, 3]
                for r in ledger["rows"]), "MATURITY_HORIZON_ORDER_MISMATCH")
    require(sum(r["original_price_only_watch"] is True for r in ledger["rows"]) == 1653,
            "ORIGINAL_WATCH_COUNT_MISMATCH")
    monitor = json.loads(restored[13010065001]["obsidian-independent-source-41122875006.json"])
    require(len(monitor["rows"]) == monitor["requested_symbols"] == 136 and
            len({r["ticker"] for r in monitor["rows"]}) == 136,
            "INDEPENDENT_MONITOR_136_NAME_DENOMINATOR_MISMATCH")
    identity = cohort_identity_report(captured_cohorts,
                                      [r["ticker"] for r in ledger["rows"]],
                                      [r["ticker"] for r in monitor["rows"]])
    return {"mode": "RESEARCH_ONLY_NOT_AN_ORDER", "pinned_zips_verified": len(rows),
            **identity,
            "rows": rows, "original_issuer_count": 8510, "original_horizon_slots": 34040,
            "independent_monitor_symbols": 136, "cross_artifact_source_links_verified": True,
            "official_closes_authenticated": False, "backup_status": "BACKUP_UNVERIFIED",
            "verified_prediction_accuracy": None, "trade_authorized": False,
            "note": "Verified downloaded ZIP bytes and internal hashes only; no off-platform durable backup or official exchange close authentication."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(audit_directory(args.artifact_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
