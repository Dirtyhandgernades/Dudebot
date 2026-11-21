"""Reproducible retrospective audit of the unchanged target-rank baseline.

No orders, production configuration, new source collection or promotion. Missing
eligibility/provenance is never filled by simulated profitability.
"""
import argparse
from collections import Counter, defaultdict
from datetime import date
from calendar import monthrange
import csv
import hashlib
import json
from pathlib import Path

from backtest.obsidian_data_audit import load_checked
from smg.models import Config
from smg.risk_model import feature_row, predict
from smg.swing_backtest import simulate
from smg.market import calendar

EXPECTED = {
    2023: (18658.11,16487.95,3,3.059),
    2024: (39124.52,25305.11,16,25.691),
    2025: (103258.54,64020.56,36,19.966),
}


def hashfile(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stats(result,packet=None):
    trades=result['trades'];profits=[float(t['pnl']) for t in trades]
    wins=[p for p in profits if p>0];losses=[p for p in profits if p<0]
    byissuer=defaultdict(float)
    for t in trades:byissuer[t['ticker']]+=t['pnl']
    net=result['net_profit'];curve=result['daily_equity']
    months={};prior=result['initial_balance']
    for month in sorted({r['date'][:7] for r in curve}):
        segment=[r for r in curve if r['date'].startswith(month)]
        end=segment[-1]['equity']
        complete=all(r['equity'] is not None for r in segment)
        year,number=map(int,month.split('-'))
        expected={str(d.date()) for d in calendar(year).sessions_in_range(month+'-01',f'{month}-{monthrange(year,number)[1]:02d}')}
        months[month]=dict(return_pct=(end/prior-1)*100 if complete and end is not None and prior is not None and prior>0 else None,
                           observed_sessions=len(segment),missing_marks=sum(r['equity'] is None for r in segment),
                           partial_month={r["date"] for r in segment}!=expected)
        prior=end if complete else None
    utilization=[];missing_exposure=0
    if packet is not None:
        inventory=[dict(t) for t in trades]+[{**p,'ticker':t} for t,p in result.get('unresolved_positions',{}).items()]
        for dayrow in curve:
            active=[t for t in inventory if t['entry_date']<=dayrow['date'] and (not t.get('exit_date') or dayrow['date']<t['exit_date'])]
            marks=[packet['split'].get(t['ticker'],{}).get(dayrow['date']) for t in active]
            if any(b is None for b in marks) or dayrow['equity'] is None or dayrow['equity']<=0:
                missing_exposure+=1;continue
            gross=sum(t['notional']*b['c']/t['adjusted_entry'] for t,b in zip(active,marks))
            utilization.append(gross/dayrow['equity'])
    allocated=sum(t.get('notional',0) for t in trades)
    concentration=max(byissuer.values(),default=0)/net if net is not None and net>0 else None
    top=sorted(wins,reverse=True)
    return dict(initial_balance=result['initial_balance'],ending_balance=result['ending_balance'],net_profit=net,
        realized_trade_profit=result['realized_profit'],interest_pnl=result['interest_pnl'],
        return_pct=100*net/result['initial_balance'] if net is not None else None,
        closed_trades=len(trades),unique_issuers=len(byissuer),wins=len(wins),losses=len(losses),
        win_rate=len(wins)/len(trades) if trades else None,
        average_win=sum(wins)/len(wins) if wins else None,average_loss=sum(losses)/len(losses) if losses else None,
        expectancy_per_trade=sum(profits)/len(profits) if profits else None,
        profit_factor=sum(wins)/-sum(losses) if losses else None,
        profit_factor_note='UNDEFINED_NO_LOSSES' if not losses else None,
        largest_individual_loss=min(profits,default=None),
        max_observed_drawdown_pct=result['max_observed_drawdown_pct'],
        missing_equity_sessions=sum(r['equity'] is None for r in curve),unresolved_positions=result['unresolved_open_positions'],
        financial_status=result['financial_status'],account_insolvent=result['account_insolvent'],
        issuer_profit=dict(sorted(byissuer.items())),largest_issuer_fraction_of_net_profit=concentration,
        largest_positive_issuer_fraction_of_positive_issuer_profit=(max(byissuer.values(),default=0)/sum(v for v in byissuer.values() if v>0)) if any(v>0 for v in byissuer.values()) else None,
        remove_top_winners_fixed_ledger={str(k):net-sum(top[:k]) if net is not None else None for k in (1,3,5)},
        removal_method='ACCOUNTING_SENSITIVITY_ONLY_NO_REALLOCATION_COUNTERFACTUAL',
        pnl_reconciliation_delta=(net-sum(profits)-result['interest_pnl']) if net is not None else None,
        monthly_marked_returns=months,coverage_gaps=result['gaps'],
        mean_daily_marked_gross_to_equity=sum(utilization)/len(utilization) if utilization else None,
        exposure_mark_missing_sessions=missing_exposure,
        realized_trade_return_on_summed_entry_notional=sum(profits)/allocated if allocated else None,
        allocated_capital_metric_note='Sum of closed entry notionals reuses capital; not portfolio equity return or SMG margin',
        unmeasured=['actual_SMG_fills','historical_permissions_and_borrow','source_authenticated_official_closes',
                    'point_in_time_market_cap','catalyst_causality','intraday_adverse_excursion','calibrated_directional_accuracy'])


def trade_audit(result,packet):
    signals={(e['signal_date'],e['ticker']):e for e in result['signal_events']}
    rows=[]
    for t in result['trades']:
        source=signals.get((t['signal_date'],t['ticker']))
        days=[d for d in packet['sessions'] if t['entry_date']<=d<=t['exit_date']]
        prices=[packet['split'].get(t['ticker'],{}).get(d) for d in days]
        complete=bool(prices) and all(prices)
        closes=[b['c']/t['adjusted_entry']-1 for b in prices] if complete else []
        adverse=max(closes+[0]) if t['side']=='SHORT' and complete else -min(closes+[0]) if complete else None
        prior_public=packet['firm_dates'].get(t['ticker'])
        rows.append({**t,'outcome_kind':'CONDITIONAL_SIMULATED_SHORT',
                     'discovery_cause':'DATED_FIRM_ASSOCIATION_PLUS_ARCHIVED_HYBRID_SIGNAL',
                     'firm_evidence_date':prior_public,'archive_firm_date_no_later_than_signal':prior_public is not None and prior_public<=t['signal_date'],
                     'matched_original_signal':source is not None,'signal_provenance':source,
                     'decision_sizing_price':source.get('decision_price') if source else None,
                     'daily_close_adverse_excursion_pct':100*adverse if adverse is not None else None,
                     'intraday_mae_verified':False,'actual_SMG_execution_verified':False,
                     'catalyst_and_counterevidence_review':'NOT_AVAILABLE_IN_ARCHIVED_SIGNAL',
                     'execution_assumption':'EOD_CLOSE_NO_INTRADAY_STOP_FILL',
                     'modeled_exposure_notional':t['notional'],
                     'fill_exceeds_intended_50000':t['notional']>50000,
                     'private_account_or_credentials_included':False})
    return rows


def score_events(source,baseline,packet,year):
    model_doc=json.loads((baseline/f'{year}-model.json').read_text())
    model=model_doc['model'];threshold=model_doc['thresholds']['top_half']
    original=json.loads((source/f'{year}-hybrid-signals.json').read_text());index={d:i for i,d in enumerate(packet['sessions'])}
    events={}
    for day,items in original.items():
        i=index[day];events[day]=[]
        for item in items:
            history=[packet['split'].get(item['ticker'],{}).get(d) for d in packet['sessions'][i-22:i]]
            features=feature_row(history) if len(history)==22 and all(history) else None
            if features is None:continue
            score=predict(model,[{'x':features}])[0]
            if score>=threshold:events[day].append({**item,'historical_rank':score})
    return events


def cached_opportunities(packet,results):
    """All cached issuer/dates, including missingness. Not full-market recall."""
    rows=[];counts=Counter();index={d:i for i,d in enumerate(packet['sessions'])}
    for year in (2023,2024,2025):
        result=results[year]
        signals={(r['signal_date'],r['ticker']) for r in result['signal_events']}
        entered={(r['signal_date'],r['ticker']) for r in result['trades']}
        for day in packet['sessions']:
            if not f'{year}-09-08'<=day<=f'{year}-12-05':continue
            i=index[day];future=packet['sessions'][i+1:i+4]
            chain=[];probe=day
            for _ in range(3):probe=str(calendar(year).next_session(probe).date());chain.append(probe)
            for ticker,series in sorted(packet['split'].items()):
                counts['cached_symbol_dates']+=1
                before=series.get(day);after=[series.get(d) for d in future]
                status='OBSERVED_NON_TARGET';decline=None
                if future!=chain or any(not f'{year}-09-08'<=d<=f'{year}-12-05' for d in future):status='HORIZON_OUTSIDE_REPLAY_WINDOW'
                elif not before or len(after)!=3 or any(not b for b in after):status='MISSING_ADJUSTED_OUTCOME_OR_REFERENCE'
                else:
                    decline=min(b['c'] for b in after)/before['c']-1
                    if decline<=-.20:status='RETROSPECTIVE_20PCT_CACHE_EVENT'
                key=(day,ticker);signaled=key in signals
                counts[status]+=1
                rows.append(dict(ticker=ticker,reference_date=day,source_status=status,adjusted_close_decline=decline,
                                 rank_signal_present=signaled,modeled_closed_trade_present=key in entered,
                                 firm_known_by_reference=packet['firm_dates'].get(ticker,'9999')<=day,
                                 comparison_warning='Reference close-to-next-3-closes differs from entry-based frozen target; descriptive only',
                                 actual_eligibility='UNKNOWN',prospective_prediction_credit=False))
    return rows,dict(counts)


def run(source,baseline,registration,out):
    source,baseline,out=Path(source),Path(baseline),Path(out)
    if out.exists():raise FileExistsError(out)
    packet,integrity=load_checked(source);spec=json.loads(Path(registration).read_text())
    if hashfile(source/'firm-timing-inputs.json.gz')!=spec['packet_sha256']:raise ValueError('REGISTERED_DATASET_HASH_MISMATCH')
    out.mkdir(parents=True)
    allstats=[];audits=[];matched=[];base_results={}
    for path in sorted(baseline.glob('20*-base.json'))+sorted(baseline.glob('20*-stress.json')):
        r=json.loads(path.read_text());s=stats(r,packet);s['variant_file']=path.name;allstats.append(s)
        for row in trade_audit(r,packet):audits.append(dict(variant_file=path.name,**row))
    reproduction=[]
    for year,expected in EXPECTED.items():
        normal=json.loads((baseline/f'{year}-top_half_30pct-50000-base.json').read_text())
        stress=json.loads((baseline/f'{year}-top_half_30pct-50000-stress.json').read_text())
        observed=(normal['net_profit'],stress['net_profit'],normal['closed_trades'],normal['max_observed_drawdown_pct'])
        ok=all(abs(a-b)<.011 for a,b in zip(observed,expected))
        reproduction.append(dict(year=year,reported=expected,reproduced=observed,matched=ok))
        if not ok:raise ValueError('BASELINE_REPRODUCTION_MISMATCH_'+str(year))
        base_results[year]=normal
        events=score_events(source,baseline,packet,year)
        for exp in [dict(id='BASE',change=dict(equity_cap=.30,decision_price_buffer=1.))]+spec['experiments']:
            for cost,bps,borrow in [('base',30,.1),('stress',100,1.)]:
                change=exp['change']
                r=simulate(packet['raw'],packet['split'],packet['cohorts'][f'{year}-09-08']['short'],packet['sessions'],
                           start=f'{year}-09-08',end=f'{year}-12-05',hold=3,strategy='FIRM_HYBRID_EXHAUSTION_RESEARCH',
                           cost_bps=bps,borrow_rate=borrow,position_target=50000,buying_power=150000,
                           firm_dates=packet['firm_dates'],firm_cfg=Config(**packet['config']),risk_controls=True,
                           signal_share_sizing=True,intraday_signals=events,smg_cash_interest=True,
                           max_position_equity_fraction=change['equity_cap'],decision_price_buffer=change['decision_price_buffer'])
                if exp['id']=='BASE':
                    reference=normal if cost=='base' else stress
                    if r['trades']!=reference['trades'] or r['daily_equity']!=reference['daily_equity']:
                        raise ValueError('REUSED_MODEL_BASELINE_NOT_IDENTICAL')
                name=f'{year}-{exp["id"]}-{cost}.json'
                (out/name).write_text(json.dumps(r,indent=2,sort_keys=True))
                matched.append(dict(year=year,experiment=exp['id'],cost_case=cost,metrics=stats(r,packet),promotion_eligible=False,
                                    blockers=['RETROSPECTIVE_ALREADY_INSPECTED_PERIODS','UNVERIFIED_HISTORICAL_EXECUTION_AND_IDENTITY']))
    opportunities,counts=cached_opportunities(packet,base_results)
    for name,rows in [('trade-audit.jsonl',audits),('cached-opportunities.jsonl',opportunities)]:
        with (out/name).open('x') as f:
            for row in rows:f.write(json.dumps(row,sort_keys=True)+'\n')
    promotion=[]
    for experiment in ('BASE','E01','E02'):
        group=[r for r in matched if r['experiment']==experiment]
        normal=[r['metrics'] for r in group if r['cost_case']=='base']
        promotion.append(dict(experiment=experiment,eligible=False,gates={
            'positive_all_normal_and_stress':'PASS' if all(r['metrics']['net_profit'] is not None and r['metrics']['net_profit']>0 for r in group) else 'FAIL',
            'profit_factor_at_least_1_3':'PASS' if all(r['metrics']['profit_factor'] is not None and r['metrics']['profit_factor']>=1.3 for r in group) else 'FAIL_OR_UNDEFINED',
            'drawdown_at_most_20_percent':'PASS' if all(r['metrics']['max_observed_drawdown_pct']<=20 for r in group) else 'FAIL',
            'no_insolvencies':'PASS' if all(not r['metrics']['account_insolvent'] for r in group) else 'FAIL',
            'issuer_share_at_most_25_percent':'PASS' if all(r['metrics']['largest_issuer_fraction_of_net_profit'] is not None and r['metrics']['largest_issuer_fraction_of_net_profit']<=.25 for r in group) else 'FAIL_OR_UNDEFINED',
            '100_independent_closed_trades':'FAIL' if sum(m['closed_trades'] for m in normal)<100 else 'UNKNOWN_DEPENDENCE',
            'three_fresh_independent_periods':'FAIL_ALREADY_INSPECTED',
            'historical_execution_identity_and_prospective_contract':'UNKNOWN_BLOCKED'},
            nominal_normal_closed_trades=sum(m['closed_trades'] for m in normal),independent_observation_count=None))
    summary=dict(promotion_review=promotion,status='ACTUAL_RETROSPECTIVE_COMPUTATION_NOT_VALIDATED_EDGE',reproduction=reproduction,
                 original_variant_count=len(allstats),original_variant_metrics=allstats,
                 trade_audit_rows=len(audits),trade_rows_are_correlated_across_variants=True,
                 cache_opportunity_counts=counts,experiments=matched,source_integrity=integrity,
                 all_models_ordinal_not_calibrated=True,production_changed=False,training_holdout_unseen=False,
                 next_action='Resolve independent historical identity/borrow/cap/marks and collect untouched later data before promotion',
                 source_hashes={str(p):hashfile(p) for p in [source/'firm-timing-inputs.json.gz',Path(registration),Path(__file__)]})
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True))
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',default='outputs/backtest/hybrid-37386241124')
    p.add_argument('--baseline',default='outputs/backtest/target-rank-2026-10-05')
    p.add_argument('--registration',default='backtest/evidence/2026-11-20/strategy-overhaul/experiment-registration.json')
    p.add_argument('--out',required=True)
    a=p.parse_args();r=run(a.source,a.baseline,a.registration,a.out)
    print(json.dumps(dict(reproduction=r['reproduction'],variants=r['original_variant_count'],trade_rows=r['trade_audit_rows'],cache_opportunities=r['cache_opportunity_counts'])))

if __name__=='__main__':main()
