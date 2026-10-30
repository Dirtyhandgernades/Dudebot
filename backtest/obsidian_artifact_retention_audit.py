"""Read-only GitHub Actions evidence-retention inventory.

RESEARCH_ONLY_NOT_AN_ORDER. GitHub artifact metadata is not the artifact bytes,
a durable off-platform backup, or independently authenticated market data.
Never count two source captures of one issuer/day as independent predictions.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

MODE = "RESEARCH_ONLY_NOT_AN_ORDER"
BRANCH = "research/obsidian-early-rug-20261025"
# Frozen October 30 receipts; never substitute a newer artifact with same name.
PINNED = (
    (41118123273, 13006897253, "ba983a61e2503b44e2e5501519ff3ee4a85be41a3312c2d1948a18175570cbc4", "PRECLOSE", 8510),
    (41140665058, 13018333034, "956448af203a64b16551f2921cac85997f53dbbceeaf725b8b816a2c5173c8bc", "MATURITY_LEDGER", 34040),
    (41071432540, 12985950392, "4baaa22217c1cdf157fc102e1aaed3238513bb94ba2c61ff3d1c72a590f18eb1", "RUG_MORNING", 8510),
    (41097562159, 12995764777, "f04e948242abbc6c6f87e36149bdd327bca3b3dadb2032be685696df95a43a96", "RUG_INTRADAY", 8510),
    (41114832467, 13006191628, "059ae485699813b940a18a3d124cd7e26ec9a817c179ce52d487b05c8c4d00b6", "RUG_DELAYED_SIP", 8510),
    (41122875045, 13008429628, "a305c830924abda6da875efaa918db6d34730298dda7394d7033df3735a8eead", "AFTERHOURS", 8510),
    (41122875006, 13010065001, "f401405bea705ea0c5cb461e168385c07206a8429f1874acde69ed02e5931359", "INDEPENDENT_HALT_MONITOR", 136),
)


def aware(value):
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return stamp if stamp.utcoffset() is not None else None


def audit(packets, as_of):
    now = aware(as_of)
    if now is None or not isinstance(packets, list):
        raise ValueError("AWARE_AS_OF_AND_RUN_PACKET_LIST_REQUIRED")
    indexed = {}
    for packet in packets:
        if not isinstance(packet, dict) or type(packet.get("run_id")) is not int or not isinstance(packet.get("artifacts"), list):
            raise ValueError("INVALID_RUN_PACKET")
        run = packet["run_id"]
        if run in indexed:
            raise ValueError("DUPLICATE_RUN_PACKET")
        indexed[run] = packet["artifacts"]
    rows = []
    for run, artifact_id, expected_sha, role, denominator in PINNED:
        matches = [a for a in indexed.get(run, []) if isinstance(a, dict) and a.get("id") == artifact_id]
        issues = []
        if len(matches) != 1:
            issues.append("ARTIFACT_MISSING_OR_DUPLICATED")
        item = matches[0] if len(matches) == 1 else {}
        if item:
            if item.get("digest") != "sha256:" + expected_sha:
                issues.append("PINNED_METADATA_DIGEST_MISMATCH")
            workflow = item.get("workflow_run")
            if not isinstance(workflow, dict) or workflow.get("id") != run or workflow.get("head_branch") != BRANCH:
                issues.append("WRONG_SOURCE_RUN_OR_BRANCH")
            if item.get("expired") is not False:
                issues.append("ARTIFACT_EXPIRED_OR_EXPIRY_UNVERIFIED")
            expires = aware(item.get("expires_at"))
            created = aware(item.get("created_at"))
            if expires is None or created is None or not created < expires:
                issues.append("INVALID_RETENTION_TIMESTAMPS")
            elif now >= expires:
                issues.append("RETENTION_DEADLINE_PASSED")
            if type(item.get("size_in_bytes")) is not int or item["size_in_bytes"] <= 0:
                issues.append("INVALID_ARTIFACT_SIZE")
        else:
            expires = None
            created = None
        rows.append({
            "role": role, "run_id": run, "artifact_id": artifact_id,
            "original_denominator_or_slots": denominator,
            "pinned_zip_sha256": expected_sha,
            "metadata_digest_matches_pinned": not issues,
            "created_at": created.isoformat() if created else None,
            "expires_at": expires.isoformat() if expires else None,
            "days_until_expiry": (expires - now).total_seconds() / 86400 if expires else None,
            "metadata_status": "METADATA_MATCH_ONLY" if not issues else "BLOCKED",
            "issues": sorted(set(issues)),
            "zip_bytes_rehashed_by_this_audit": False,
            "off_platform_backup_verified": False,
            "actual_official_close_authenticated": False,
        })
    return {
        "mode": MODE, "as_of": now.isoformat(), "original_capture_status_unchanged": True,
        "pinned_artifacts": len(PINNED),
        "metadata_matched_count": sum(not row["issues"] for row in rows),
        "blocked_count": sum(bool(row["issues"]) for row in rows),
        "earliest_expiry": min((row["expires_at"] for row in rows if row["expires_at"]), default=None),
        "backup_status": "BACKUP_UNVERIFIED",
        "official_closes_authenticated": False,
        "verified_predictions": None, "trade_authorized": False,
        "issuer_day_events_deduplicated_for_performance": None,
        "note": "Metadata hashes are not independently rehashed ZIP bytes. All seven roles are distinct receipts, not seven prediction cohorts.",
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-json", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit(json.loads(Path(args.metadata_json).read_text()), args.as_of)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"pinned_artifacts": result["pinned_artifacts"], "metadata_matched_count": result["metadata_matched_count"], "blocked_count": result["blocked_count"], "backup_status": result["backup_status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
