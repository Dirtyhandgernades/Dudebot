"""Offline research packet contract tests."""
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone

from backtest.obsidian_early_discovery_packet import build_packet, write_once

T = datetime(2026, 10, 27, 19, 50, tzinfo=timezone.utc)


class PacketTests(unittest.TestCase):
    def test_no_scan_cannot_create_prospective_catch(self):
        p = build_packet({"snapshots": []}, [{"ticker":"CPIX"}], [], [
            {"ticker":"XP", "kind":"CHAT_REFERENCE",
             "source_ref":"dated-chat", "observation_date":"2026-10-26"}
        ])
        self.assertEqual(p["coverage"]["manifest_symbols"], 1)
        self.assertEqual(p["coverage"]["off_manifest_observed"], 1)
        self.assertFalse(p["full_market_denominator_verified"])
        self.assertFalse(p["early_catch_or_edge_demonstrated"])

    def test_preserve_unknown_snapshot(self):
        p = build_packet({"snapshots":[{"ticker":"CPIX","phase":"PRECLOSE",
                                        "observed_at":T.isoformat()}]}, [], [])
        self.assertEqual(p["snapshots_received"], 1)
        self.assertEqual(p["snapshots_preserved"], 1)
        self.assertEqual(p["lane_counts"], {"QUOTE_OR_PRIOR_CLOSE_UNVERIFIED":1})

    def test_invalid_snapshot_is_quarantined_not_silently_dropped(self):
        p = build_packet({"snapshots":[{"ticker":"XP", "observed_at":None}]}, [], [])
        self.assertEqual(p["snapshots_preserved"], 1)
        self.assertEqual(p["lane_counts"], {"QUARANTINED_INVALID_INPUT":1})

    def test_future_outcome_features_rejected(self):
        for field in ("future_close", "realized_return", "exit_price", "winner"):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    build_packet({"snapshots":[{"ticker":"CPIX",field:10}]},[],[])

    def test_duplicate_identity_not_silently_deduplicated(self):
        r={"ticker":"CPIX", "phase":"PRECLOSE", "observed_at":T.isoformat()}
        with self.assertRaises(ValueError):
            build_packet({"snapshots":[r,r]},[],[])

    def test_write_once_preserves_original_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/"report.json"
            write_once(target, {"status":"RESEARCH_ONLY_NOT_AN_ORDER"})
            original=target.read_bytes()
            with self.assertRaises(FileExistsError):
                write_once(target, {"status":"MODIFIED"})
            self.assertEqual(target.read_bytes(), original)


    def test_nested_forward_and_realized_fields_rejected(self):
        nested = [
            {"quote": {"future_close": 4.2}},
            {"tape": {"support_loss": {"realized_pnl": 900}}},
            {"catalyst": {"forward_return": -0.4}},
            {"metadata": {"outcome_label": "winner"}},
            {"quote": {"labels": ["future_winner"]}},
        ]
        for fields in nested:
            with self.subTest(fields=fields):
                with self.assertRaisesRegex(ValueError, "FUTURE_OUTCOME_LEAKAGE_FIELD"):
                    build_packet({"snapshots": [{"ticker": "CPIX", **fields}]}, [], [])

    def test_root_and_reference_future_labels_rejected(self):
        with self.assertRaisesRegex(ValueError, "FUTURE_OUTCOME_LEAKAGE_FIELD"):
            build_packet({"snapshots": [], "forward_close": 3}, [], [])
        with self.assertRaisesRegex(ValueError, "FUTURE_OUTCOME_LEAKAGE_FIELD"):
            build_packet({"snapshots": []}, [], [],
                         [{"ticker": "CPIX", "kind": "CHAT_REFERENCE",
                           "source_ref": "audit", "future_return": -0.3}])


if __name__=="__main__":
    unittest.main()
