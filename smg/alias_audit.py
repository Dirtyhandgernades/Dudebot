"""Two bounded historical-symbol probes; reference diagnostics, never screening."""
import csv,json
from pathlib import Path
from .cli import settings
from .backtest import audit_reference_market,resolve_sample_gaps,write_json

def main():
    root=Path.cwd();cfg,_=settings(root)
    with (root/'backtest/reference_events.csv').open() as stream:events=list(csv.DictReader(stream))
    review=json.loads((root/'backtest/reference_gap_review.json').read_text())
    pairs=[]
    for item in review['records']:
        if item['diagnosis']!='LATER_TICKER_LABEL':continue
        for event in events:
            if event['ticker']==item['ticker'] and event['event_date']==item['event_date']:
                pairs.append((event,dict(event,ticker=item['historical_symbol']),item))
    state=root/'backtest/runtime/alias-audit'
    samples=audit_reference_market([p[1] for p in pairs],cfg,state,budget=2)
    gaps={r['event_id']:r for r in resolve_sample_gaps(samples,cfg,state,budget=2)}
    records=[]
    for (original,query,review),sample in zip(pairs,samples):
        wider=gaps.get(sample['event_id'])
        available=sample['status']=='BARS_AVAILABLE_IN_SAMPLE' or bool(wider and wider['status'] in {'SAME_SESSION_HISTORY_AVAILABLE','OLDER_DAILY_HISTORY_ONLY'})
        records.append(dict(event_id=original['event_id'],reference_ticker=original['ticker'],queried_ticker=query['ticker'],
            event_date=original['event_date'],label_source=review['source_url'],sample=sample,wider_check=wider,
            status='HISTORICAL_SYMBOL_BARS_AVAILABLE' if available else 'GAP_REMAINS',
            limitation='Later source diagnoses a reference label. It is not pre-drop screening evidence or a detection.'))
    result=dict(notification_timezone=cfg.notification_timezone,feed=cfg.market_feed,delay_minutes=cfg.market_data_delay_minutes,
        reference_unchanged=True,records=records,actual_detections=None,actual_misses=None)
    write_json(root/'reports/alias-audit.json',result)
    print(json.dumps(result))

if __name__=='__main__':main()
