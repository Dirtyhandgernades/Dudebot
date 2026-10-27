"""Write-once offline OBSIDIAN discovery research packet builder.

This is not a scanner, market connection, trading alert or order system.
Does not retrieve historical outcomes, credentials, or future prices.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .obsidian_early_discovery import (
    OUTPUT_MODE, reconcile_coverage, prioritize_early_discovery,
)


_LEAKAGE_PREFIXES = ("future_", "next_close", "outcome_", "realized_", "profit_", "pnl_")

def _reject_future_labels(value):
    """Fail closed on outcome/forward-label keys anywhere in a research packet."""
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError("NONSTRING_EVIDENCE_KEY")
            normalized = key.casefold()
            if (normalized.startswith(_LEAKAGE_PREFIXES + ("forward_", "subsequent_"))
                    or normalized in {"winner", "label", "labels", "exit_price",
                                      "best_future_close"}):
                raise ValueError("FUTURE_OUTCOME_LEAKAGE_FIELD")
            _reject_future_labels(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _reject_future_labels(child)



def build_packet(packet, master_rows, supplemental_rows, reference_rows=()):
    if not isinstance(packet, dict):
        raise ValueError("EXPECTED_PACKET_OBJECT")
    _reject_future_labels(packet)
    snapshots = packet.get("snapshots", [])
    if not isinstance(snapshots, list):
        raise ValueError("SNAPSHOTS_MUST_BE_LIST")
    if not isinstance(packet.get("observations", []), list):
        raise ValueError("OBSERVATIONS_MUST_BE_LIST")
    all_observations = list(reference_rows) + packet.get("observations", [])
    _reject_future_labels(all_observations)
    ledger = reconcile_coverage(
        master_rows, supplemental_rows, all_observations,
        decision_cutoff=packet.get("decision_cutoff"),
        scan_inventory=packet.get("scan_inventory", []),
    )
    evaluated = []
    distinct = set()
    for n, row in enumerate(snapshots):
        if not isinstance(row, dict):
            raise ValueError("SNAPSHOT_MUST_BE_OBJECT")
        if any(str(k).lower().startswith(_LEAKAGE_PREFIXES) or
               str(k).lower() in {"winner", "label", "exit_price", "best_future_close"}
               for k in row):
            raise ValueError("FUTURE_OUTCOME_LEAKAGE_FIELD")
        quote_source = row.get("quote") or {}
        if not isinstance(quote_source, dict):
            raise ValueError("QUOTE_MUST_BE_OBJECT")
        identity = (row.get("ticker"), str(row.get("observed_at")),
                    row.get("phase"), quote_source.get("source_id"))
        if identity in distinct:
            raise ValueError("DUPLICATE_OBSERVATION_IDENTITY")
        distinct.add(identity)
        try:
            result = prioritize_early_discovery(row)
        except (ValueError, TypeError, KeyError):
            result = {
                "ticker": row.get("ticker"), "observed_at": None,
                "lane": "QUARANTINED_INVALID_INPUT",
                "priority_ordinal_not_probability": None,
                "hard_eligibility_confirmed": False,
                "potentially_executable": False,
                "prospective_prediction_credited": False,
                "execution_status": OUTPUT_MODE,
            }
        evaluated.append({"input_index": n, **result})
    ordered = sorted(evaluated,
                     key=lambda x: (x["priority_ordinal_not_probability"] is None,
                                    x["priority_ordinal_not_probability"] or 99,
                                    x.get("observed_at") or "",
                                    str(x.get("ticker"))))
    counts = Counter(x["lane"] for x in evaluated)
    packet_digest = hashlib.sha256(json.dumps(packet, sort_keys=True,
                                    separators=(",", ":"), default=str).encode()).hexdigest()
    return {
        "mode": OUTPUT_MODE,
        "packet_sha256": packet_digest,
        "snapshots_received": len(snapshots),
        "snapshots_preserved": len(evaluated),
        "lane_counts": dict(sorted(counts.items())),
        "research_priorities_not_orders": ordered,
        "coverage": ledger,
        "screen_is_authenticated_by_tool": False,
        "full_market_denominator_verified": False,
        "early_catch_or_edge_demonstrated": False,
        "results_not_available_until_future_independent_closes": True,
    }


def write_once(path, value):
    """Exclusive creation; a completed research packet is never silently replaced."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, indent=2, sort_keys=True) + "\n"
    with target.open("x", encoding="utf-8") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Offline OBSIDIAN research packet; no orders or HTTP")
    parser.add_argument("--packet", required=True, help="Timestamped independent evidence JSON")
    parser.add_argument("--output", required=True, help="New immutable research report JSON")
    parser.add_argument("--master", default="backtest/obsidian_historical_watchlist_manifest_2026_10_26.json")
    parser.add_argument("--supplemental", default="backtest/obsidian_supplemental_watchlist_2026_10_26.json")
    parser.add_argument("--references", default="backtest/obsidian_oct26_observation_provenance.json")
    args = parser.parse_args()
    load = lambda path: json.loads(Path(path).read_text(encoding="utf-8"))
    report = build_packet(load(args.packet), load(args.master)["records"],
                          load(args.supplemental)["records"], load(args.references)["observations"])
    write_once(args.output, report)
    print(json.dumps({key: report[key] for key in (
        "mode", "packet_sha256", "snapshots_received", "snapshots_preserved", "lane_counts",
        "full_market_denominator_verified")}, sort_keys=True))


if __name__ == "__main__":
    main()
