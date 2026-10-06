"""Predeclared chronological timing comparison over cached independent inputs.

No reference/friend labels or future returns select candidates. Daily features
are complete at signal close, so entry is the NEXT session close. Previously
inspected years are diagnostics; issuer separation is an additional check,
not an untouched date holdout. No automatic live promotion.
"""
import argparse
import csv
import gzip
import hashlib
import json
import math
from collections import Counter,defaultdict
from datetime import date,timedelta
from pathlib import Path
import numpy as np
import yaml

from smg.decision_evidence import execution_evidence
from smg.game_rules import is_excluded_symbol
from smg.market import calendar,session_bounds
from smg.mechanism_audit import compact_records,roles_before,news_before,news_topics,longer_ramp_watch
from smg.risk_model import feature_row,earliest_firm_dates,predict,metrics
from smg.validation import fit_calibration,calibrated_scores,reliability

FEATURES=('return21','return5','return1','drawdown21','log_volume_ratio','failed_low','range',
          'upper_wick','close_location','peak_age','volume_trend','realized_volatility','long_ramp',
          'public_underwriter','public_auditor','public_counsel','financing_news','distress_news')


def held_issuer(ticker,cik=None):
    key='CIK:'+str(int(cik)) if cik is not None else 'TICKER:'+ticker
    return int(hashlib.sha256(key.encode()).hexdigest()[:8],16)%5==0


def independent_rows(rows):
    kept=[];ends={}
    for row in sorted(rows,key=lambda r:(r['signal_date'],r['ticker'])):
        key='CIK:'+row['issuer_cik'] if row.get('issuer_cik') else 'TICKER:'+row['ticker']
        if row['signal_date']<=ends.get(key,''):continue
        kept.append(row);ends[key]=row['label_end']
    return kept


def features(history,long_history,links,news):
    base=feature_row(history)
    if base is None:return None
    last=history[-1];span=last['h']-last['l'];peak=max(range(22),key=lambda i:history[i]['h'])
    returns=[history[i]['c']/history[i-1]['c']-1 for i in range(1,22)]
    old=sum(b['v'] for b in history[-11:-6])/5;recent=sum(b['v'] for b in history[-6:-1])/5
    roles={r['role'] for r in links if not r['relationship_at_source'].startswith('FORMER_PARTY')}
    topics=news_topics(news)
    x=base[:4]+[math.log1p(max(0,base[4]))]+base[5:]+[
        (last['h']-max(last.get('o',last['c']),last['c']))/span if span>0 else 0,
        (last['c']-last['l'])/span if span>0 else .5,(21-peak)/21,
        math.log1p(recent/old) if old>0 else 0,float(np.std(returns)),float(longer_ramp_watch(long_history)),
        float(bool(roles&{'underwriter','placement_agent'})),float('auditor' in roles),float('counsel' in roles),
        float('FINANCING_MENTION' in topics),float('CORPORATE_OR_DISTRESS_EVENT' in topics)]
    return x if all(math.isfinite(v) for v in x) else None


def build_rows(packet,records):
    sessions=packet['sessions'];raw=packet['raw'];split=packet['split'];first=earliest_firm_dates(records)
    # Legacy packet dates are independently sourced too; never extend from audit labels.
    for ticker,day in packet['first_dates'].items():first[ticker]=min(day,first.get(ticker,day))
    by_ticker=defaultdict(list)
    for r in records:by_ticker[r['ticker']].append(r)
    identity_ends={r['old_symbol']:r['effective_date'] for r in packet.get('renames',[]) if r.get('status')=='STITCHED_RENAME'}
    discontinuities=[0]
    for i in range(len(sessions)-1):
        expected=str(calendar(int(sessions[i][:4])).next_session(sessions[i]).date())
        discontinuities.append(discontinuities[-1]+int(expected!=sessions[i+1]))
    rows=[];gaps=Counter()
    for ticker,public_day in sorted(first.items()):
        if is_excluded_symbol(ticker) or (len(ticker)==5 and ticker.isalpha()):gaps['HARD_SYMBOL_EXCLUSION']+=1;continue
        series=split.get(ticker,{});unadjusted=raw.get(ticker,{})
        ciks={str(int(r['cik'])) for r in by_ticker[ticker] if r.get('cik') and str(r['cik']).isdigit()}
        cik=next(iter(ciks)) if len(ciks)==1 else None
        if not series:gaps['INDEPENDENT_SYMBOL_WITHOUT_PRICE_HISTORY']+=1;continue
        for i in range(21,len(sessions)-4):
            day=sessions[i]
            if day>=identity_ends.get(ticker,'9999-99-99'):continue
            if day<public_day:continue
            if discontinuities[i+4]!=discontinuities[i-21]:gaps['NONCONTIGUOUS_SESSIONS']+=1;continue
            price=(unadjusted.get(day) or {}).get('c')
            if price is None:gaps['RAW_SIGNAL_PRICE_MISSING']+=1;continue
            if price<=3:continue
            history=[series.get(d) for d in sessions[i-21:i+1]]
            if not all(history):gaps['FEATURE_WINDOW_MISSING']+=1;continue
            long=[series.get(d) for d in sessions[max(0,i-62):i+1]]
            links=roles_before(by_ticker,ticker,day)
            news=news_before(packet['news'].get(ticker,[]),day)
            x=features(history,long,links,news)
            if x is None:gaps['FEATURES_INVALID']+=1;continue
            # No strict candle prerequisite: rank the broad short/long ramp watch.
            if not (x[0]>=.12 or x[1]>=.20 or x[12]):continue
            span=sessions[i+1:i+5]
            outcome_complete=all(d in series for d in span)
            if not outcome_complete:gaps['ENTRY_OR_OUTCOME_MISSING']+=1
            # Missing future bars are a pending/unavailable label, not a
            # reason to erase an otherwise observable earlier candidate.
            decline=min(series[d]['c'] for d in span[1:])/series[span[0]]['c']-1 if outcome_complete else None
            warning_days=sessions[i+1:i+4]
            warning_label=int(min(series[d]['c'] for d in warning_days)/history[-1]['c']-1<=-.20+1e-10) if all(d in series for d in warning_days) else None
            close=session_bounds(date.fromisoformat(day))[1]
            evidence=execution_evidence(ticker,close.isoformat(),price)
            rows.append({'ticker':ticker,'signal_date':day,'entry_date':span[0],'label_end':span[-1],
                         'x':x,'label':int(decline<=-.20+1e-10) if decline is not None else None,'max_decline_1_3':decline,
                         'same_close_warning_label':warning_label,
                         'raw_signal_price':price,'decision_at':close.isoformat(),'held_issuer':held_issuer(ticker,cik),'issuer_cik':cik,
                         'execution':evidence['status'],'execution_gaps':evidence['missing'],
                         'dated_firms':links,'news_ids':[r['id'] for r in news]})
    return rows,dict(gaps),first


def train_model(rows,width):
    if len(rows)<30 or len({r['label'] for r in rows})<2:return None
    x=np.asarray([r['x'][:width] for r in rows],float);y=np.asarray([r['label'] for r in rows],float)
    # Fixed clipping avoids letting a single split/microfloat extreme set the scale.
    x=np.clip(x,-20,20);mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-10]=1
    z=(x-mean)/scale;w=np.zeros(width);b=math.log((y.sum()+.5)/(len(y)-y.sum()+.5))
    for _ in range(700):
        p=1/(1+np.exp(-np.clip(z@w+b,-35,35)));err=p-y
        w-=.05*((z.T@err)/len(y)+.1*w);b-=.05*err.mean()
    return {'features':FEATURES[:width],'mean':mean.tolist(),'scale':scale.tolist(),'weights':w.tolist(),
            'bias':float(b),'training_samples':len(rows),'training_positives':int(y.sum()),
            'training_latest_label':max(r['label_end'] for r in rows),'class_weighting':'NONE',
            'clip_min':-20,'clip_max':20}


def scores(model,rows):
    if not model or not rows:return []
    return predict(model,[{'x':np.clip(r['x'][:len(model['features'])],-20,20).tolist()} for r in rows])


def portfolio(rows,raw,split,sessions,year,strict=False,cost_bps=30,borrow_rate=.1):
    """Conditional research cash/collateral ledger; no actual order/borrow claim."""
    start=f'{year}-09-08';end=f'{year}-12-05';days=[d for d in sessions if start<=d<=end]
    indices={d:i for i,d in enumerate(sessions)};queued=defaultdict(list)
    for r in rows:
        if strict and r['execution']!='EXECUTABLE_INDICATION':continue
        queued[r['entry_date']].append(r)
    cash=100000.;positions={};trades=[];curve=[];gaps=Counter();peak=cash;drawdown=0.;fee=cost_bps/10000
    def marked(day):
        if any(day not in split[t] for t in positions):return None
        return cash+sum(p['notional']*(2-split[t][day]['c']/p['adjusted_entry']) for t,p in positions.items())
    for day in days:
        i=indices[day];previous=sessions[i-1];decision_equity=marked(previous)
        prev_exposure=sum(p['notional']*split[t][previous]['c']/p['adjusted_entry'] for t,p in positions.items()) if decision_equity is not None else 0
        decision_room=max(0,min(150000,1.5*(decision_equity or 0))-prev_exposure)
        for ticker,p in list(positions.items()):
            prior=split[ticker].get(previous);prior_return=1-prior['c']/p['adjusted_entry'] if prior else None
            reason='GAME_END' if day==days[-1] else 'THREE_SESSION_LIMIT' if day>=p['planned_exit'] else 'STOP_FROM_PRIOR_CLOSE' if prior_return is not None and prior_return<=-.12 else 'TARGET_FROM_PRIOR_CLOSE' if prior_return is not None and prior_return>=.20 else None
            if reason is None:continue
            if day not in split[ticker]:gaps['MISSING_EXIT_PRICE']+=1;continue
            ratio=split[ticker][day]['c']/p['adjusted_entry'];gross=p['notional']*(1-ratio)
            exit_fee=p['notional']*ratio*fee+5;borrow=p['notional']*borrow_rate*(date.fromisoformat(day)-date.fromisoformat(p['entry_date'])).days/365
            net=gross-p['entry_fee']-exit_fee-borrow;cash+=p['notional']+gross-exit_fee-borrow
            trades.append({**p,'ticker':ticker,'exit_date':day,'exit_reason':reason,'pnl':round(net,2),'return_pct':100*net/p['notional']})
            del positions[ticker]
        if day!=days[-1] and decision_equity is not None and decision_equity>0:
            for row in sorted(queued.get(day,[]),key=lambda r:(-r['score'],r['ticker'])):
                ticker=row['ticker']
                if ticker in positions or len(positions)>=10:continue
                entry=raw[ticker].get(day);adjusted=split[ticker].get(day);equity=marked(day)
                if not entry or not adjusted or equity is None:gaps['MISSING_FILL_OR_CAPITAL']+=1;continue
                if entry['c']<=3:gaps['ENTRY_BELOW_3']+=1;continue
                budget=min(50000,.30*decision_equity,decision_room)
                # Reserve 20% for a closing-price move BEFORE placing shares.
                # This is a fixed sensitivity policy, not a guaranteed cap.
                shares=math.floor(max(0,budget)/(row['raw_signal_price']*1.20))
                if shares<10:continue
                notional=shares*entry['c'];entry_fee=notional*fee+5
                exposure=sum(p['notional']*split[t][day]['c']/p['adjusted_entry'] for t,p in positions.items())
                room=min(150000,1.5*max(0,equity))-exposure
                # A next-close price jump can make stale-price shares exceed
                # the intended position size even when total buying power fits.
                if notional>min(50000,.30*decision_equity):gaps['POSITION_TARGET_EXCEEDED_AT_FILL']+=1
                if notional+entry_fee>room:gaps['ORDER_REJECTED_AT_FILL']+=1;continue
                cash-=notional+entry_fee;decision_room=max(0,decision_room-shares*row['raw_signal_price']*1.20*(1+fee)-5)
                positions[ticker]={'signal_date':row['signal_date'],'entry_date':day,'planned_exit':sessions[min(i+3,indices[days[-1]])],
                                   'entry_price':entry['c'],'adjusted_entry':adjusted['c'],'shares':shares,'notional':notional,
                                   'entry_fee':entry_fee,'score':row['score'],'execution':row['execution']}
        equity=marked(day)
        if equity is not None:peak=max(peak,equity);drawdown=max(drawdown,(peak-equity)/peak)
        curve.append({'date':day,'equity':equity,'open_positions':len(positions)})
    final=cash if not positions else None
    return {'status':'STRICT_EVIDENCE_LEDGER' if strict else 'CONDITIONAL_RESEARCH_ONLY','initial':100000,
            'ending_balance':round(final,2) if final is not None else None,'net_profit':round(final-100000,2) if final is not None else None,
            'closed_trades':len(trades),'trades':trades,'max_drawdown_pct':100*drawdown,'open_positions':positions,
            'cost_bps_each_way':cost_bps,'assumed_annual_borrow_rate':borrow_rate,'commission_per_order':5,
            'position_target':50000,'decision_equity_cap':.30,'assumed_gross_buying_power':150000,
            'decision_price_buffer':1.20,
            'gaps':dict(gaps),'curve':curve,'live_enabled':False,
            'limitations':['Daily features imply next-close entry; no same-close hindsight fill',
                           'Conditional results lack verified historical cap/halt/borrow/SMG membership',
                           'Cash interest, game-specific margin mechanics and dividends not certified']}


def evaluate(rows,packet,out):
    results=[];out.mkdir(parents=True,exist_ok=True)
    for year in (2023,2024,2025):
        cutoff=f'{year}-01-01';cal_start=str(date(year,1,1)-timedelta(days=180))
        prior_days=sorted({r['signal_date'] for r in rows if r['label'] is not None and r['label_end']<cutoff and not r['held_issuer']})
        # A short initial packet must not reserve virtually all earlier bars
        # for calibration. Choose this split using dates only, never outcomes.
        if prior_days:cal_start=max(cal_start,prior_days[min(len(prior_days)-1,int(.70*len(prior_days)))])
        # Hold 20% of tickers out from BOTH fit and calibration, deterministically.
        train=independent_rows([r for r in rows if r['label'] is not None and r['label_end']<cal_start and not r['held_issuer']])
        calibration=independent_rows([r for r in rows if r['label'] is not None and cal_start<=r['signal_date'] and r['label_end']<cutoff and not r['held_issuer']])
        test=[r for r in rows if f'{year}-09-08'<=r['signal_date'] and r['label_end']<=f'{year}-12-05']
        for name,width in [('CORE_PRICE',7),('STRUCTURE_AND_DATED_CONTEXT',len(FEATURES)),
                           ('STRUCTURE_WITH_COOLING_GUARD',len(FEATURES))]:
            model=train_model(train,width)
            if not model:
                results.append({'year':year,'model':name,'status':'INSUFFICIENT_PRIOR_TRAINING','training_windows':len(train)});continue
            cal_scores=scores(model,calibration);calibrator=fit_calibration(calibration,cal_scores)
            threshold=float(np.quantile(scores(model,train),.90))
            predicted=scores(model,test)
            def timing(r):return name!='STRUCTURE_WITH_COOLING_GUARD' or (-.12<=r['x'][2]<=.10 and r['x'][8]<=.65)
            selected=[{**r,'score':s} for r,s in zip(test,predicted) if s>=threshold and timing(r)]
            known_test=[r for r in test if r['label'] is not None]
            independent=independent_rows(known_test);ind_scores=scores(model,independent)
            hold=[r for r in independent if r['held_issuer']]
            calibrated=calibrated_scores(calibrator,ind_scores)
            base_rate=sum(r['label'] for r in calibration)/len(calibration) if calibration else None
            brier=sum((s-r['label'])**2 for r,s in zip(independent,calibrated))/len(independent) if calibrated else None
            constant=sum((base_rate-r['label'])**2 for r in independent)/len(independent) if independent and base_rate is not None else None
            reasons=[]
            if len(independent)<50:reasons.append('TOO_FEW_INDEPENDENT_WINDOWS')
            if sum(r['label'] for r in independent)<10:reasons.append('TOO_FEW_POSITIVE_OUTCOMES')
            if not hold or sum(r['label'] for r in hold)<5:reasons.append('HELD_ISSUER_EVIDENCE_INSUFFICIENT')
            if brier is None or constant is None or brier>=constant:reasons.append('NO_CALIBRATION_SKILL_ABOVE_CONSTANT')
            selected_windows=[r for r,s in zip(independent,ind_scores) if s>=threshold and timing(r)]
            result={'year':year,'model':name,'training_windows':len(train),'calibration_windows':len(calibration),
                    'training_latest_label':model['training_latest_label'],'calibration_latest_label':max((r['label_end'] for r in calibration),default=None),
                    'threshold_source':'Fixed 90th percentile of prior TRAINING scores, not future profit',
                    'rank_threshold':threshold,'warning_same_close_positives':sum(r['same_close_warning_label'] or 0 for r in independent),
                    'next_close_entry_positives':sum(r['label'] for r in independent),
                    'all_daily':metrics(known_test,scores(model,known_test),threshold),'independent_windows':metrics(independent,ind_scores,threshold),
                    'unavailable_outcome_candidates':len(test)-len(known_test),
                    'timing_guard':'Prior return between -12% and +10%; close in lower 65% of range' if name.endswith('GUARD') else None,
                    'selected_independent_windows':len(selected_windows),
                    'selected_window_precision':sum(r['label'] for r in selected_windows)/len(selected_windows) if selected_windows else None,
                    'held_issuer_windows':metrics(hold,scores(model,hold),threshold),'calibrated_brier':brier,'constant_brier':constant,
                    'confidence_gate':'FAIL' if reasons else 'RETROSPECTIVE_DIAGNOSTIC_PASS_NOT_LIVE_APPROVAL',
                    'gate_reasons':reasons,'confidence_sizing_enabled':False,'live_enabled':False,
                    'execution_counts':dict(Counter(r['execution'] for r in selected))}
            models={'rank_model':model,'calibration':calibrator}
            (out/f'{year}-{name}-model.json').write_text(json.dumps(models,indent=2))
            for case,bps,borrow,strict in [('base',30,.1,False),('stress',100,1.,False),('strict',30,.1,True)]:
                p=portfolio(selected,packet['raw'],packet['split'],packet['sessions'],year,strict,bps,borrow)
                (out/f'{year}-{name}-{case}.json').write_text(json.dumps(p,indent=2))
                result[case]={k:p[k] for k in ('ending_balance','net_profit','closed_trades','max_drawdown_pct')}
            # Future labels annotate what was missed; they never alter the
            # earlier rank, threshold or action. Keep losses and unknowns too.
            decisions=[]
            for r,s in zip(test,predicted):
                action='SELECTED_RESEARCH' if s>=threshold and timing(r) else 'TIMING_GUARD_REJECTED' if s>=threshold else 'RANK_BELOW_PRIOR_THRESHOLD'
                decisions.append({'ticker':r['ticker'],'signal_date':r['signal_date'],'entry_date':r['entry_date'],
                                  'label_end':r['label_end'],'rank_score':s,'rank_threshold':threshold,'action':action,
                                  'outcome_20pct_after_entry':r['label'],'same_close_warning_outcome':r['same_close_warning_label'],
                                  'held_issuer':r['held_issuer'],'execution_status':r['execution'],
                                  'execution_gaps':'|'.join(r['execution_gaps'])})
            if decisions:
                with (out/f'{year}-{name}-decisions.csv').open('w',newline='',encoding='utf-8') as f:
                    writer=csv.DictWriter(f,fieldnames=list(decisions[0]));writer.writeheader();writer.writerows(decisions)
            result['missed_after_entry_positives']=sum(d['outcome_20pct_after_entry']==1 and d['action']!='SELECTED_RESEARCH' for d in decisions)
            result['decision_actions']=dict(Counter(d['action'] for d in decisions))
            result['reliability']=reliability(independent,calibrated) if calibrated else {'status':'CALIBRATION_UNAVAILABLE'}
            results.append(result)
    return results


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--packet',required=True);parser.add_argument('--records',nargs='*',default=[])
    parser.add_argument('--out',default='outputs/backtest/repair-2026-10-06');args=parser.parse_args()
    raw_bytes=Path(args.packet).read_bytes();packet=json.loads(gzip.decompress(raw_bytes));records=list(packet['records'])
    entities=yaml.safe_load(Path('config/entities.yaml').read_text())
    records.extend(compact_records(args.records,entities));rows,gaps,first=build_rows(packet,records)
    out=Path(args.out);results=evaluate(rows,packet,out)
    with gzip.open(out/'observations.json.gz','wt',encoding='utf-8') as f:json.dump(rows,f)
    summary={'status':'REUSED_HISTORY_RESEARCH_NOT_LIVE_VALIDATION','input_sha256':hashlib.sha256(raw_bytes).hexdigest(),
             'candidate_symbols':len(first),'sampled_symbols':len({r['ticker'] for r in rows}),'rows':len(rows),
             'source_record_count':len(records),'gaps':gaps,'results':results,'unavailable_labels':sum(r['label'] is None for r in rows),
             'live_enabled':False,'frozen_forward_changed':False,'market_requests':0,
             'limitations':['All tested years previously inspected','Issuer split uses unique source CIK where present; unresolved CIKs fall back to symbol',
                            'Bounded news corpus is incomplete; absence of a headline is not absence of an event',
                            'Historical execution evidence missing; strict portfolios must not assume availability']}
    gates=[]
    for name in ('CORE_PRICE','STRUCTURE_AND_DATED_CONTEXT','STRUCTURE_WITH_COOLING_GUARD'):
        by_year={r['year']:r for r in results if r['model']==name}
        failures=['FRESH_PROSPECTIVE_OUTCOMES_REQUIRED','HISTORICAL_EXECUTION_UNVERIFIED']
        for year in (2023,2024,2025):
            row=by_year.get(year,{})
            if not row.get('base'):failures.append(f'{year}_INSUFFICIENT_DATA');continue
            if row['base']['net_profit'] is None or row['base']['net_profit']<=0:failures.append(f'{year}_BASE_NOT_PROFITABLE')
            if row['stress']['net_profit'] is None or row['stress']['net_profit']<=0:failures.append(f'{year}_STRESS_NOT_PROFITABLE')
            if row['confidence_gate']=='FAIL':failures.append(f'{year}_STATISTICAL_GATE_FAILED')
        gates.append({'model':name,'status':'BLOCKED','reasons':failures,'live_enabled':False})
    summary['promotion_gates']=gates
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({**{k:summary[k] for k in ('candidate_symbols','sampled_symbols','rows','gaps')},
                      'results':[{k:r[k] for k in ('year','model','status') if k in r}|{k:r[k] for k in ('base','stress','strict','confidence_gate','held_issuer_windows') if k in r} for r in results]}),flush=True)


if __name__=='__main__':main()
