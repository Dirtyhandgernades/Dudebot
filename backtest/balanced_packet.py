"""Merge independently discovered dated sources; fill historical prices once."""
import argparse,gzip,json
from pathlib import Path
from smg.risk_model import earliest_firm_dates
from smg.swing_backtest import download
from smg.market import calendar
from smg.game_rules import is_excluded_symbol
from smg.history_identity import repair_legacy_volume
from backtest.extend_training_inputs import align_early_history


def merge_records(packet,records):
    seen={(r['ticker'],r['decision_at'],r.get('source_url')) for r in packet['records']}
    identities={}
    for r in packet['records']:
        if r.get('cik'):identities.setdefault(r['ticker'],set()).add(str(int(r['cik'])))
    added=[];conflicts=[]
    for r in records:
        if (r['ticker'],r['decision_at'],r.get('source_url')) in seen:continue
        cik=str(int(r['cik'])) if r.get('cik') else None
        if identities.get(r['ticker']) and cik not in identities[r['ticker']]:
            conflicts.append({'ticker':r['ticker'],'cik':cik,'reason':'TICKER_REUSE_OR_IDENTITY_INTERVAL_UNRESOLVED'});continue
        added.append(r)
        if cik:identities.setdefault(r['ticker'],set()).add(cik)
    packet['records']+=added
    first=earliest_firm_dates(packet['records'])
    improved={}
    for ticker,day in first.items():
        old=packet['first_dates'].get(ticker)
        if old is None or day<old:
            packet['first_dates'][ticker]=day;improved[ticker]={'before':old,'after':day}
    return added,improved,conflicts


def main():
    p=argparse.ArgumentParser();p.add_argument('--packet',required=True);p.add_argument('--records',required=True)
    p.add_argument('--out',default='reports/balanced');p.add_argument('--collect',action='store_true');a=p.parse_args()
    packet=repair_legacy_volume(json.loads(gzip.decompress(Path(a.packet).read_bytes())))
    added,improved,conflicts=merge_records(packet,json.loads(Path(a.records).read_text()))
    symbols=sorted(t for t in packet['first_dates'] if not is_excluded_symbol(t) and not(len(t)==5 and t.isalpha()))
    requests=0;alignment={}
    if a.collect:
        # Old cache starts2022 for many symbols. A fixed2021/22 training
        # lookback needs earlier sources AND prices, not just more2025 bars.
        missing=[t for t in symbols if not packet['raw'].get(t) or
                 (packet['first_dates'][t]<'2023-01-01' and min(packet['raw'][t])>'2021-01-01')]
        cache=Path('backtest/runtime/balanced-bars');cache.mkdir(parents=True,exist_ok=True)
        extra,requests=download(missing,'2020-10-01','2025-12-05',cache)
        alignment=align_early_history(packet,extra)
    # calendar2024 covers2020–2025; calendar2025 begins2021 and cannot warm
    # the first2021feature windows with actual late2020sessions.
    packet['sessions']=[str(d.date()) for d in calendar(2024).sessions_in_range('2020-10-01','2025-12-05')]
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    with gzip.open(out/'inputs.json.gz','wt',encoding='utf-8') as stream:json.dump(packet,stream)
    summary={'added_records':len(added),'earlier_or_new_independent_dates':improved,'independent_symbols':len(packet['first_dates']),
             'provider_requests':requests,'price_alignment':alignment,'live_changed':False,
             'identity_conflicts':conflicts,
             'limits':['No missing prices/borrow/cap/halts are imputed','No reference/friend stock selection','Not a approved replacement of pinned live training corpus']}
    (out/'collection.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='earlier_or_new_independent_dates'}))


if __name__=='__main__':main()
