"""Post-run friend/reference comparison, never an input to discovery or trading."""
import argparse
import csv
import gzip
import json
from pathlib import Path


def compare(folder, transactions):
    folder=Path(folder)
    data=json.loads(gzip.decompress((folder/'firm-timing-inputs.json.gz').read_bytes()))
    sessions=data['sessions'];index={d:i for i,d in enumerate(sessions)}
    orders=[r for r in transactions if r['transaction_type']=='SHORT SELL' and
            '2025-09-08'<=r['date']<='2025-12-05']
    friends={r['ticker'] for r in orders};reports={}
    for strategy in ['LIVE_FIRM_TIMING_SHORT','FIRM_EXHAUSTION_RESEARCH']:
        result=json.loads((folder/f'2025-{strategy}.json').read_text())
        trades=result['trades'];signals=result['signal_events'];rows=[]
        for ticker in sorted(friends):
            own=[r for r in orders if r['ticker']==ticker]
            first=data['firm_dates'].get(ticker)
            known=bool(first and any(first<=r['date'] for r in own))
            ticker_trades=[t for t in trades if t['ticker']==ticker]
            aligned=[]
            for trade in ticker_trades:
                for order in own:
                    if order['date'] in index and trade['entry_date'] in index:
                        lead=index[order['date']]-index[trade['entry_date']]
                        if 0<=lead<=2:aligned.append(trade)
            signal_near=any(s['ticker']==ticker and s['signal_date'] in index and
                            any(o['date'] in index and 1<=index[o['date']]-index[s['signal_date']]<=5 for o in own)
                            for s in signals)
            reason=('FIRM_DISCOVERY_ABSENT' if first is None else
                    'FIRM_SOURCE_TOO_LATE' if not known else
                    'ENTRY_ALIGNED_WITH_FRIEND' if aligned else
                    'TRADED_OTHER_DATES' if ticker_trades else
                    'NO_CLOSED_TRADE_DESPITE_PRIOR_FIRM_SOURCE')
            rows.append({'ticker':ticker,'friend_first_entry':min(r['date'] for r in own),
                         'first_independent_firm_date':first,'watched_before_friend_entry':known,
                         'has_signal_1_to_5_sessions_before_friend_entry':signal_near,
                         'bot_closed_trades':len(ticker_trades),'bot_entry_same_or_1_2_sessions_before_friend':bool(aligned),
                         'conditional_pnl_all_bot_trades':round(sum(t['pnl'] for t in ticker_trades),2),
                         'comparison_result':reason})
        reports[strategy]={'friend_short_tickers':len(friends),
            'watched_before_friend_entry':sum(r['watched_before_friend_entry'] for r in rows),
            'ticker_trade_overlap':sum(r['bot_closed_trades']>0 for r in rows),
            'entry_aligned_tickers':sum(r['bot_entry_same_or_1_2_sessions_before_friend'] for r in rows),
            'target_70_percent_tickers':42 if len(friends)==60 else __import__('math').ceil(len(friends)*.7),
            'net_profit':result['net_profit'],'closed_trades':result['closed_trades'],
            'rows':rows,'selection_uses_friend_inputs':False,
            'limitations':['Friend trades are evaluation examples, not proof of fraud or 20% future declines',
                           'Ticker overlap and nearby entry dates are not profitable pre-drop detection',
                           'Historical borrow, cap, halts and game executions remain unverified']}
        fields=list(rows[0]) if rows else []
        if fields:
            with (folder/f'{strategy}-friend-comparison.csv').open('w',newline='',encoding='utf-8') as handle:
                writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows(rows)
        fields=['ticker','entry_date','exit_date','signal_date','shares','notional','entry_price',
                'exit_reason','pnl','return_pct','timing_trigger']
        with (folder/f'{strategy}-trade-ledger.csv').open('w',newline='',encoding='utf-8') as handle:
            writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader()
            writer.writerows({k:t.get(k) for k in fields} for t in trades)
    (folder/'friend-comparison-summary.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    return reports


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report-folder',required=True)
    parser.add_argument('--friend-transactions',required=True);args=parser.parse_args()
    with Path(args.friend_transactions).open(newline='',encoding='utf-8-sig') as handle:transactions=list(csv.DictReader(handle))
    reports=compare(args.report_folder,transactions)
    print(json.dumps({k:{n:v for n,v in r.items() if n not in ('rows','limitations')} for k,r in reports.items()},indent=2))


if __name__=='__main__':main()
