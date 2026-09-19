import csv
import json

from smg.replay_report import render


def test_combined_report_preserves_holdout_and_does_not_upgrade_conditional_matches(tmp_path):
    replay = tmp_path / "replay"; replay.mkdir()
    reference = tmp_path / "reference.csv"
    reference.write_text("event_id,ticker,event_date,reported_drop_pct,source\ne1,ABC,2024-01-02,-40,user\n")
    message = tmp_path / "message.txt"; message.write_text("ABC\t1/2/2024\t-40%\n")
    with (replay / "event_comparison.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["event_id","ticker","event_date","result","sampled_decisions"])
        writer.writeheader(); writer.writerow(dict(event_id="e1",ticker="ABC",event_date="2024-01-02",
            result="CONDITIONAL_FIRM_AND_PRICE_MATCH",sampled_decisions=3))
    (replay / "strict_event_comparison.json").write_text(json.dumps([dict(event_id="e1",ticker="ABC",
        event_date="2024-01-02",result="NOT_EVALUABLE",evaluated_candidate_decisions=0,reasons="NO_REPLAY_RECORDS_IN_LOOKBACK")]))
    (replay / "summary.json").write_text(json.dumps(dict(comparison_counts={"CONDITIONAL_FIRM_AND_PRICE_MATCH":1},limitations=["cap unknown"])))
    (replay / "strict_summary.json").write_text(json.dumps(dict(transaction_candidates=0,evaluated_decisions=0,
        planned_decisions=0,limitations=["halt unknown"])))
    text, rows = render(replay, reference, message)
    assert "Fully verified strict detections: 0" in text
    assert rows[0]["firm_first"] == "CONDITIONAL_FIRM_AND_PRICE_MATCH"
