"""Compare first intraday firm signals with pre-close signals on the same universe.

Historical five-minute data are downloaded once per season and reused at all
checkpoints. Future prices never nominate a checkpoint candidate or a signal.
"""
import argparse
import gzip
import json
from collections import Counter,defaultdict
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from smg.intraday_replay import Bars,partial_bar,hybrid_event,scaled_hybrid_events
from smg.game_rules import is_excluded_symbol
from smg.market import session_bounds
from smg.risk_model import samples,fit,predict,feature_row,matured_before
from smg.swing_backtest import simulate
from smg.history_identity import repair_legacy_volume
from backtest.repair_study import fixed_trade_cost_sensitivity


def points(day):
    opened,closed=session_bounds(date.fromisoformat(day))
    values={opened+timedelta(minutes=x) for x in (90,210,330)}|{closed-timedelta(minutes=20)}
    return sorted(p for p in values if opened+timedelta(minutes=30)<=p<closed)


def at_point(packet,ticker,day,raw_rows,split_rows,decision,cfg):
    opened,_=session_bounds(date.fromisoformat(day));cutoff=decision-timedelta(minutes=16)
    raw=partial_bar(raw_rows,opened,cutoff);adjusted=partial_bar(split_rows,opened,cutoff)
    if not raw or not adjusted:return None
    # Same-security alias series may have different provider adjustment units.
    for change in packet.get('renames',[]):
        if change.get('status')=='STITCHED_RENAME' and ticker==change['new_symbol'] and day>=change['effective_date']:
            adjusted={**adjusted,**{k:adjusted[k]*change['adjusted_scale'] for k in ('o','h','l','c')}}
            adjusted['v']/=change['adjusted_scale']
    event=hybrid_event(packet,ticker,day,adjusted,raw,cfg)
    if event:
        event.update(decision_at=decision.isoformat(),data_cutoff=cutoff.isoformat(),
                     checkpoint_from_open_minutes=(decision-opened).total_seconds()/60)
    return event


def run(packet,client,out,train_window_years=None):
    out.mkdir(parents=True,exist_ok=True);packet=repair_legacy_volume(packet);packet={**packet,'firm_dates':packet['first_dates']}
    sessions=packet['sessions'];index={d:i for i,d in enumerate(sessions)};results=[];public={}
    for row in packet['records']:
        if 'VERIFIED_LISTED_FIRM_RELATIONSHIP' not in row.get('reasons',[]):continue
        try:stamp=datetime.fromisoformat(row['decision_at'].replace('Z','+00:00'))
        except (TypeError,ValueError):continue
        if stamp.tzinfo is not None:public[row['ticker']]=min(stamp,public.get(row['ticker'],stamp))
    ends={r['old_symbol']:r['effective_date'] for r in packet.get('renames',[]) if r.get('status')=='STITCHED_RENAME'}
    labels=samples(packet['records'],packet['raw'],packet['split'],sessions,firm_dates=packet['first_dates'])
    cfg=SimpleNamespace(surge_return_min_pct=12)
    for year in (2023,2024,2025):
        train=matured_before(labels,f'{year}-01-01',f'{year-train_window_years}-01-01' if train_window_years else None);model=fit(train)
        if not model:results.append({'year':year,'status':'TRAINING_UNAVAILABLE'});continue
        threshold=float(np.quantile(predict(model,train),.5));candidate_days={};scores={};gaps=Counter()
        for day in sessions:
            if not f'{year}-09-08'<=day<=f'{year}-12-05':continue
            i=index[day];candidate_days[day]=[]
            for ticker,first in packet['first_dates'].items():
                if first>day or day>=ends.get(ticker,'9999-99-99') or is_excluded_symbol(ticker) or (len(ticker)==5 and ticker.isalpha()):continue
                prior=sessions[i-22:i];raw=packet['raw'].get(ticker,{}).get(prior[-1])
                history=[packet['split'].get(ticker,{}).get(d) for d in prior]
                if not raw or raw['c']<=3 or not all(history) or history[-1]['c']<history[0]['c']:continue
                x=feature_row(history)
                if x is None:continue
                score=predict(model,[{'x':x}])[0]
                if score<threshold:continue
                candidate_days[day].append(ticker);scores[(day,ticker)]=score
        symbols=sorted({t for ts in candidate_days.values() for t in ts})
        start=datetime(year,9,1,tzinfo=timezone.utc);end=datetime(year,12,6,tzinfo=timezone.utc)
        try:
            raw=client.get(symbols,start,end,'raw');adjusted=client.get(symbols,start,end,'split')
        except RuntimeError as exc:
            results.append({'year':year,'status':'DATA_REQUEST_BUDGET','detail':str(exc)});continue
        indexed={}
        for mode,data in [('raw',raw),('split',adjusted)]:
            grouped=defaultdict(lambda:defaultdict(list))
            for ticker,rows in data.items():
                for bar in rows:grouped[ticker][bar['t'][:10]].append(bar)
            indexed[mode]=grouped
        early={};late={};confirmed_then_late={};all_events={};point_counts=Counter()
        for day,tickers in candidate_days.items():
            early[day]=[];late[day]=[];confirmed_then_late[day]=[];all_events[day]=[];checkpoints=points(day)
            for ticker in tickers:
                chosen=None;confirmed=None;late_fallback=None
                for point in checkpoints:
                    if ticker in public and public[ticker]>point:continue
                    if ticker not in public and day==packet['first_dates'][ticker]:continue
                    event=at_point(packet,ticker,day,indexed['raw'][ticker][day],indexed['split'][ticker][day],point,cfg)
                    if not event:gaps['NO_SETUP_OR_PRICE_WINDOW']+=1;continue
                    event['training_rank']=scores[(day,ticker)]
                    all_events[day].append(event)
                    prior=packet['raw'][ticker][sessions[index[day]-1]]['c']
                    change=event['decision_price']/prior-1
                    if confirmed is None and change<=.02:confirmed={**event,'position_scale':1.,'entry_filter':'OBSERVED_GAIN_AT_MOST_2_PERCENT'}
                    if chosen is None:chosen=event;point_counts[point.hour*60+point.minute]+=1
                    if point==checkpoints[-1]:
                        late[day].append(event);late_fallback={**event,'position_scale':.5,'entry_filter':'DEFERRED_PRECLOSE_HALF_TARGET'}
                if chosen:early[day].append(chosen)
                if confirmed or late_fallback:confirmed_then_late[day].append(confirmed or late_fallback)
        (out/f'{year}-all-checkpoint-signals.json').write_text(json.dumps(all_events,indent=2))
        scaled,_=scaled_hybrid_events(packet,early)
        for policy,events in [('PRECLOSE_ONLY',late),('FIRST_INTRADAY_SIGNAL',early),('FIRST_SIGNAL_UPMOVE_HALF_SIZE',scaled),
                              ('CONFIRMED_EARLY_OR_DEFERRED_HALF',confirmed_then_late)]:
            (out/f'{year}-{policy}-signals.json').write_text(json.dumps(events,indent=2))
            row={'year':year,'policy':policy,'candidate_symbols':len(symbols),'candidate_symbol_days':sum(map(len,candidate_days.values())),
                 'rank_threshold':threshold,'training_latest_label':max(r['label_end'] for r in train),
                 'first_checkpoint_counts_utc_minutes':dict(point_counts),'gaps':dict(gaps),'live_enabled':False}
            for case,bps,borrow in [('base',30,.1),('stress',100,1.)]:
                p=simulate(packet['raw'],packet['split'],symbols,sessions,start=f'{year}-09-08',end=f'{year}-12-05',
                    strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',hold=3,firm_dates=packet['first_dates'],
                    intraday_signals=events,signal_share_sizing=True,risk_controls=True,position_target=50000,
                    buying_power=150000,max_position_equity_fraction=.30,decision_price_buffer=1.2,
                    smg_cash_interest=True,cost_bps=bps,borrow_rate=borrow)
                if case=='base':base=p
                (out/f'{year}-{policy}-{case}.json').write_text(json.dumps(p,indent=2))
                row[case]={k:p[k] for k in ('net_profit','ending_balance','closed_trades','max_observed_drawdown_pct')}
            row['same_trade_stress']=fixed_trade_cost_sensitivity({**base,'open_positions':base.get('unresolved_positions',{})},packet['split'])
            results.append(row);print(json.dumps(row),flush=True)
    report={'status':'FOUR_CHECKPOINT_RESEARCH','results':results,'requests':client.requests,'training_window_years':train_window_years,
            'limits':['Partial independent firm corpus, not verified historical trade eligibility',
                      'Checkpoint comparisons are inspected retrospective hypotheses','No borrow/cap/halt facts imputed']}
    (out/'summary.json').write_text(json.dumps(report,indent=2));return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--packet',required=True);parser.add_argument('--out',default='reports/intraday-checkpoints')
    parser.add_argument('--train-window-years',type=int,choices=[2,3]);args=parser.parse_args()
    run(json.loads(gzip.decompress(Path(args.packet).read_bytes())),Bars('backtest/runtime/checkpoint-bars',max_requests=500),Path(args.out),args.train_window_years)


if __name__=='__main__':main()
