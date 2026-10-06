"""Frozen prospective firm forecast log. No orders and no Discord sends."""
import hashlib
import json
from collections import Counter
from datetime import date,datetime,timedelta
from pathlib import Path
from types import SimpleNamespace
from .game_rules import APPROVED_EXCHANGES,is_excluded_symbol,eligibility
from .intraday_replay import hybrid_event
from .market import calendar,session_bounds
from .risk_model import feature_row,predict
from .shortability import executable_short
from .validation import calibrated_scores,reliability


def verify_implementation(spec):
    root=Path(__file__).resolve().parents[1]
    for name,digest in spec.get('implementation_sha256',{}).items():
        path=(root/name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or hashlib.sha256(path.read_text(encoding='utf-8').encode()).hexdigest()!=digest:
            raise ValueError('FROZEN_IMPLEMENTATION_CHANGED; register a new experiment version')


def contract(store,path,now):
    payload=Path(path).read_bytes();spec=json.loads(payload)
    digest=hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':')).encode()).hexdigest();old=store.get('forward_contract:'+spec['id'])
    verify_implementation(spec)
    if old and old['sha256']!=digest:raise ValueError('FROZEN_FORWARD_CONTRACT_CHANGED; use a new version')
    frozen=datetime.fromisoformat(spec['frozen_at'])
    bounds=session_bounds(date.fromisoformat(spec['start_date']))
    if frozen.tzinfo is None or frozen>now or not bounds or frozen>=bounds[0]:
        raise ValueError('Forward contract must be frozen before its first session')
    if spec.get('live_trade_enabled') or spec.get('confidence_sizing_enabled'):
        raise ValueError('Prospective shadow contract cannot enable live trading or confidence sizing')
    if not old:store.put('forward_contract:'+spec['id'],{'sha256':digest,'spec':spec,'registered_at':now.isoformat()})
    return spec,digest


def capture(store,evaluations,now,cfg,path):
    spec,digest=contract(store,path,now);day=str(now.date());counts=Counter()
    bounds=session_bounds(now.date())
    if not spec['start_date']<=day<=spec['end_date'] or not bounds or not (
            bounds[1]-timedelta(minutes=spec['decision_window_minutes_before_close'])<=now<bounds[1]):
        return {'status':'OUTSIDE_FORWARD_WINDOW','contract_id':spec['id'],'forecasts':0}
    prior=[str(d.date()) for d in calendar(now.year).sessions_in_range(now.date()-timedelta(days=60),now.date()-timedelta(days=1))][-22:]
    for e in evaluations:
        c=e.candidate
        if c.pipeline!='FIRM_WATCH':continue
        key='forward_forecast:'+spec['id']+':'+day+':'+c.ticker
        if store.get(key):counts['ALREADY_CAPTURED']+=1;continue
        if (is_excluded_symbol(c.ticker) or (len(c.ticker)==5 and c.ticker.isalpha()) or
                c.is_acquisition_corp is not False or c.exchange not in APPROVED_EXCHANGES or not e.matches):
            counts['STRUCTURE_OR_HARD_EXCLUSION']+=1;continue
        s=e.snapshot
        if s is None or not s.research_history or not s.research_partial:
            counts['FEATURE_DATA_UNAVAILABLE']+=1;continue
        if [r['date'] for r in s.research_history]!=prior:
            counts['NONCONSECUTIVE_FEATURE_HISTORY']+=1;continue
        if (s.feed!='sip' or s.declared_delay_minutes!=spec['data_delay_minutes'] or
                now-s.asof<timedelta(minutes=spec['data_delay_minutes']) or
                now-s.asof>timedelta(minutes=spec['data_delay_minutes']+5) or
                not 0<=(s.asof-s.price_time).total_seconds()<=300 or
                'CORPORATE_ACTION_REVIEW' in s.flags):
            counts['DATA_CONTRACT_MISMATCH']+=1;continue
        history={r['date']:r for r in s.research_history}
        packet={'sessions':prior+[day],'split':{c.ticker:history}}
        event=hybrid_event(packet,c.ticker,day,s.research_partial,s.research_partial,
                           SimpleNamespace(surge_return_min_pct=cfg.surge_return_min_pct))
        if not event:counts['NO_TIMING_SETUP']+=1;continue
        score=predict(spec['model'],[{'x':feature_row(s.research_history)}])[0]
        selected=score>=spec['rank_threshold']
        game_status,game_reasons=eligibility(s,cfg,now)
        clear=bool(e.halt and e.halt.status=='CLEAR' and 0<=(now-e.halt.checked_at).total_seconds()<=300)
        borrow=executable_short(e.shortability)
        can_paper=selected and game_status is None and clear and borrow
        event.update(decision_at=now.isoformat(),data_cutoff=s.asof.isoformat(),signal_date=day)
        # Forecasts stay immutable. Calibration estimates are experimental
        # diagnostics; the frozen confidence gate stays disabled.
        row={'contract_id':spec['id'],'contract_sha256':digest,'ticker':c.ticker,'signal_date':day,
            'observed_at':now.isoformat(),'rank_score':score,'selected':selected,'paper_eligible':can_paper,
            'game_status':game_status,'game_reasons':game_reasons,'halt_clear':clear,'borrow_executable':borrow,
            'experimental_calibration_estimate':calibrated_scores(spec.get('calibration'),[score])[0] if spec.get('calibration') else None,
            'confidence_sizing_enabled':False,'event':event,
            'feature_basis':'REGULAR_SESSION_MINUTE_AGGREGATES; differs from provider daily training',
            'history':s.research_history,'snapshot_price':s.price}
        store.put(key,row);counts['SELECTED' if selected else 'RANK_REJECTED']+=1
        counts['PAPER_ELIGIBLE' if can_paper else 'PAPER_BLOCKED']+=1
    store.put('forward_capture:last',{'at':now.isoformat(),'contract_id':spec['id'],'counts':dict(counts)})
    return {'status':'CAPTURED','contract_id':spec['id'],'counts':dict(counts)}


def review(store,bars,today,now,raw_bars=None):
    contracts=store.items('forward_contract:');reports=[]
    for kind,data in (('split',bars),('raw',raw_bars or {})):
        for ticker,series in data.items():
            key='forward_prices:'+kind+':'+ticker
            cached=store.get(key,{})
            cached.update({d:b for d,b in series.items() if d<=today})
            store.put(key,cached)
    for _,bundle in contracts:
        spec=bundle['spec'];forecasts=[v for _,v in store.items('forward_forecast:'+spec['id']+':')]
        try:verify_implementation(spec)
        except ValueError:
            reports.append({'contract_id':spec['id'],'status':'FROZEN_IMPLEMENTATION_CHANGED','confidence_sizing_enabled':False})
            continue
        rows=[]
        for f in forecasts:
            series=store.get('forward_prices:split:'+f['ticker'],{});day=f['signal_date'];start=date.fromisoformat(day)
            existing=store.get('forward_outcome:'+spec['id']+':'+day+':'+f['ticker'])
            if existing and existing['label_complete']:
                rows.append(existing);continue
            future=[str(d.date()) for d in calendar(start.year).sessions_in_range(start+timedelta(days=1),start+timedelta(days=15))][:3]
            base=series.get(day);known=[(d,series[d]) for d in future if d<=today and d in series]
            complete=base is not None and len(known)==3
            missing=[d for d in [day]+future if d<=today and d not in series]
            hit=bool(base and base['c']>0 and known and min(b['c'] for _,b in known)/base['c']-1<=-.20+1e-10)
            status='HIT_20_PERCENT' if hit else 'MATURED_NO_20_PERCENT' if complete else 'DATA_GAP' if missing else 'PENDING'
            row={k:f[k] for k in ('ticker','signal_date','rank_score','selected','paper_eligible','experimental_calibration_estimate')}
            row.update(outcome=status,label=int(hit) if complete or hit else None,label_complete=complete,
                       missing_sessions=missing,reviewed_at=now.isoformat())
            store.put('forward_outcome:'+spec['id']+':'+day+':'+f['ticker'],row);rows.append(row)
        counts=Counter(r['outcome'] for r in rows);mature=[r for r in rows if r['label_complete']]
        selected=[r for r in mature if r['selected']]
        estimated=[r for r in mature if r['experimental_calibration_estimate'] is not None]
        calibration=reliability(estimated,[r['experimental_calibration_estimate'] for r in estimated]) if estimated else None
        prevalence=sum(r['label'] for r in mature)/len(mature) if mature else None
        gate={'minimum_matured':50,'minimum_positive_outcomes':10,'minimum_distinct_tickers':5}
        gate.update(spec.get('confidence_gate',{}))
        reasons=[]
        if len(mature)<gate['minimum_matured']:reasons.append('INSUFFICIENT_PROSPECTIVE_SAMPLE')
        if sum(r['label'] for r in mature)<gate['minimum_positive_outcomes']:reasons.append('INSUFFICIENT_POSITIVE_OUTCOMES')
        if len({r['ticker'] for r in mature})<gate['minimum_distinct_tickers']:reasons.append('INSUFFICIENT_ISSUER_DIVERSITY')
        baseline_brier=prevalence*(1-prevalence) if prevalence is not None else None
        if not calibration or baseline_brier is None or calibration['brier']>=baseline_brier:
            reasons.append('NO_PROSPECTIVE_CALIBRATION_SKILL_OVER_CONSTANT_BASELINE')
        report={'contract_id':spec['id'],'contract_sha256':bundle['sha256'],'reviewed_at':now.isoformat(),
            'status':'PENDING_PROSPECTIVE_OUTCOMES' if not mature else 'PROSPECTIVE_RESEARCH',
            'forecasts':len(rows),'counts':dict(counts),'matured':len(mature),'selected_matured':len(selected),
            'selected_hits':sum(r['label'] for r in selected),
            'precision':sum(r['label'] for r in selected)/len(selected) if selected else None,
            'calibration':calibration,'confidence_sizing_enabled':False,'rows':rows}
        report['confidence_gate']={'status':'REVIEW_ELIGIBLE' if not reasons else 'NOT_READY',
            'reasons':reasons,'constant_prevalence_brier':baseline_brier,'thresholds':gate,
            'automatic_live_promotion':False}
        report['paper_portfolios']=paper_portfolios(store,spec,forecasts,today)
        store.put('forward_report:'+spec['id'],report);reports.append(report)
    return reports


def paper_portfolios(store,spec,forecasts,today):
    from .swing_backtest import simulate
    if not forecasts or today<spec['start_date']:return {'status':'PENDING_PROSPECTIVE_FORECASTS'}
    begin=date.fromisoformat(spec['start_date'])
    sessions=[str(d.date()) for d in calendar(begin.year).sessions_in_range(begin-timedelta(days=70),spec['end_date'])]
    raw={};split={};events={};names=set()
    for f in forecasts:
        ticker=f['ticker'];names.add(ticker)
        # Prior regular-session bars are warm-up marks, never substitutes for
        # a missing entry/exit close. Final raw/split bars are fetched nightly.
        raw.setdefault(ticker,{}).update({b['date']:b for b in f['history'] if b['date']<spec['start_date']})
        split.setdefault(ticker,{}).update({b['date']:b for b in f['history'] if b['date']<spec['start_date']})
        if f['paper_eligible']:events.setdefault(f['signal_date'],[]).append(f['event'])
    for ticker in names:
        raw[ticker].update(store.get('forward_prices:raw:'+ticker,{}))
        split[ticker].update(store.get('forward_prices:split:'+ticker,{}))
    portfolios={}
    for name,profile in spec['profiles'].items():
        result=simulate(raw,split,sorted(names),sessions,start=spec['start_date'],end=min(today,spec['end_date']),
            strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',hold=3,firm_dates={t:spec['start_date'] for t in names},
            signal_share_sizing=True,risk_controls=True,intraday_signals=events,smg_cash_interest=True,
            liquidate_at_end=today>=sessions[-1],**profile)
        # A running forward test retains open positions instead of liquidating
        # every review day. Report cash-derived balance only when fully closed.
        result['status']='PAPER_RESEARCH_UNVERIFIED_SMG_EXECUTION'
        result['open_positions']=result['unresolved_positions']
        store.put('forward_portfolio:'+spec['id']+':'+name,result)
        portfolios[name]={k:result[k] for k in ('ending_balance','marked_ending_equity','realized_profit',
            'closed_trades','unresolved_open_positions','max_observed_drawdown_pct','gaps')}
    return portfolios
