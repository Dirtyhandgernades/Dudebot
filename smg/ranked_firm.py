"""Independent ranked firm signal layer; no orders or percentage confidence.

Prior completed provider daily features match the historical rank inputs.
Actual delayed five-minute observations revalidate the setup. The original
failed daily-breakdown proxy and frozen forward experiment remain separate.
"""
import argparse
import hashlib
import json
import os
from datetime import datetime,timedelta,timezone
from pathlib import Path
from .cli import settings,required_env
from .models import Candidate,Snapshot,HaltCheck
from .firm_first import firm_structure
from .game_rules import eligibility,NasdaqMarketCaps
from .rules import EntityList,normalize_name
from .risk_model import feature_row,predict
from .market import calendar,session_bounds
from .intraday_replay import Bars,partial_bar,hybrid_event
from .shortability import executable_short
from .transport import Http
from .storage import Store,GitHubState
from .notify import DiscordSender
from .adaptive_firm import apply_active
from .adaptive_firm import context as adaptive_context
from .drop_probability import estimate

UTC=timezone.utc


def daily_history(store,http,symbols,now):
    today=now.date();cal=calendar(today.year)
    prior=str(cal.previous_session(str(cal.date_to_session(today,direction='next').date())).date())
    bounds=session_bounds(today)
    if bounds and now>=bounds[1]+timedelta(minutes=16):prior=str(today)
    cache=store.get('ranked_daily_history',{})
    if cache.get('date')!=str(today) or cache.get('through')!=prior:cache={'date':str(today),'through':prior,'raw':{},'split':{}}
    missing=[t for t in symbols if t not in cache['raw'] or t not in cache['split']];requests=0
    headers={'APCA-API-KEY-ID':required_env('ALPACA_API_KEY'),'APCA-API-SECRET-KEY':required_env('ALPACA_SECRET_KEY')}
    for mode in ('raw','split'):
        query={'symbols':','.join(missing),'timeframe':'1Day','start':str(today-timedelta(days=90)),
               'end':prior+'T23:59:59Z','adjustment':mode,'asof':'-','feed':'sip','limit':10000}
        seen=set()
        while missing:
            data=http.json('https://data.alpaca.markets/v2/stocks/bars',params=query,headers=headers);requests+=1
            for ticker,bars in data.get('bars',{}).items():
                cache[mode].setdefault(ticker,{}).update({r['t'][:10]:r for r in bars if r['t'][:10]<=prior})
            token=data.get('next_page_token')
            if not token:break
            if token in seen or requests>=12:raise ValueError('DAILY_HISTORY_PAGINATION_BUDGET')
            seen.add(token);query['page_token']=token
        for ticker in missing:cache[mode].setdefault(ticker,{})
    store.put('ranked_daily_history',cache)
    return cache,requests


def valid_policy(spec,root,now):
    for name,digest in spec.get('implementation_sha256',{}).items():
        path=(root/name).resolve()
        if not path.is_relative_to(root) or hashlib.sha256(path.read_text(encoding='utf-8').encode()).hexdigest()!=digest:
            raise ValueError('RANKED_POLICY_IMPLEMENTATION_CHANGED')
    if spec.get('confidence_sizing_enabled'):raise ValueError('Confidence sizing cannot be enabled')
    if spec.get('first_session') and now.date().isoformat()<spec['first_session']:return False
    return bool(spec.get('enabled'))


def association_structure(candidate,cfg,entities,now):
    """An association watch need not pretend an old auditor is still engaged."""
    result=firm_structure(candidate,cfg,entities,now)
    soft={'RELATIONSHIP_CHANGE_REVIEW_REQUIRED','NO_VERIFIED_ENTITY_MATCH'}
    if result.status=='REVIEW_REQUIRED' and set(result.reasons)<=soft:
        matches=[]
        for item in candidate.matches:
            role='underwriter' if item.role=='placement_agent' else item.role
            entry=entities.entries.get((role,normalize_name(item.name)))
            if entry and item.evidence.filed_at<=now.date():
                matches.append({**entry,'role':item.role,'relationship':'historical/source-dated association; current engagement unconfirmed',
                                'evidence':item.evidence.model_dump(mode='json')})
        if matches:result.status='STRUCTURAL_MATCH';result.matches=matches;result.reasons=['VERIFIED_LISTED_FIRM_RELATIONSHIP','CURRENT_ENGAGEMENT_UNCONFIRMED']
    return result


def eligible_signal(candidate,history,raw_history,adjusted_partial,raw_partial,now,cfg,entities,policy,borrow,halt,cap=None):
    result=association_structure(candidate,cfg,entities,now);result.shortability=borrow;result.halt=halt
    if halt and halt.status=='HALTED':result.status='EXCLUDED';result.reasons.append('CURRENTLY_HALTED');return result
    if result.status!='STRUCTURAL_MATCH':return result
    bounds=session_bounds(now.date())
    if not bounds or not bounds[0]+timedelta(minutes=90)<=now<bounds[1]:
        result.status='MARKET_NOT_CONFIRMED';result.reasons.append('OUTSIDE_TESTED_INTRADAY_WINDOW');return result
    cutoff=now-timedelta(minutes=16)
    if not adjusted_partial or not raw_partial:return result.model_copy(update={'status':'REVIEW_REQUIRED','reasons':['CURRENT_PRICE_WINDOW_UNAVAILABLE']})
    observed=datetime.fromisoformat(raw_partial['last_complete_at'])
    if not 0<=(cutoff-observed).total_seconds()<=300:return result.model_copy(update={'status':'REVIEW_REQUIRED','reasons':['STALE_OR_FUTURE_PRICE']})
    if len(history)!=22 or len(raw_history)!=22 or any(r['date']>=str(now.date()) for r in history):
        result.status='REVIEW_REQUIRED';result.reasons.append('PRIOR_DAILY_FEATURES_UNAVAILABLE');return result
    if raw_history[-1]['c']<=3:return result.model_copy(update={'status':'REVIEW_REQUIRED','reasons':['PRIOR_PRICE_OUTSIDE_MODEL_SCOPE']})
    x=feature_row(history)
    if x is None:return result.model_copy(update={'status':'REVIEW_REQUIRED','reasons':['DAILY_FEATURES_INVALID']})
    score=predict(policy['model'],[{'x':x}])[0]
    result.ranking_evidence['ranked_firm']={'policy_id':policy['id'],'rank_score':score,'threshold':policy['rank_threshold'],
                                         'is_probability':False,'features':x,'feature_dates':[r['date'] for r in history]}
    result.rank=[min(m['priority'] for m in result.matches),-len(result.matches),-score]
    if score<policy['rank_threshold']:
        result.status='MARKET_NOT_CONFIRMED';result.reasons.append('PRIOR_TRAINED_RANK_BELOW_THRESHOLD');return result
    packet={'sessions':[r['date'] for r in history]+[str(now.date())],'split':{candidate.ticker:{r['date']:r for r in history}}}
    event=hybrid_event(packet,candidate.ticker,str(now.date()),adjusted_partial,raw_partial,cfg)
    if not event:result.status='MARKET_NOT_CONFIRMED';result.reasons.append('NO_FIRM_EXHAUSTION_SETUP');return result
    change=raw_partial['c']/raw_history[-1]['c']-1
    mode=policy['entry_policy']
    event.update(decision_at=now.isoformat(),data_cutoff=cutoff.isoformat())
    fraction=(observed-bounds[0])/(bounds[1]-bounds[0]);average=sum(r['v'] for r in history[-20:])/20
    rvol=adjusted_partial['v']/fraction/average if fraction>0 and average>0 else None
    snapshot=Snapshot(asof=cutoff,price_time=observed,price=raw_partial['c'],
        monthly_return=100*(adjusted_partial['c']/history[1]['c']-1),
        five_day_return=100*(adjusted_partial['c']/history[-5]['c']-1),one_day_return=100*(adjusted_partial['c']/history[-1]['c']-1),
        drawdown_pct=100*(adjusted_partial['c']/max([r['h'] for r in history]+[adjusted_partial['h']])-1),
        rvol=rvol,rvol20=rvol,baseline_sessions=20,cumulative_volume=raw_partial['v'],baseline_volume=average*fraction,
        source_url='https://data.alpaca.markets/v2/stocks/bars',feed='sip',declared_delay_minutes=16,
        flags=['UNIFORM_TIME_VOLUME_PROJECTION','DELAYED_MARKET_DATA','RANK_IS_NOT_PERCENTAGE_CONFIDENCE'])
    if cap:cap.apply(candidate,snapshot,now)
    result.snapshot=snapshot
    if any('ads ratio' in n.lower() or 'ticker change' in n.lower() for n in candidate.notes):
        result.status='REVIEW_REQUIRED';result.reasons.append('CORPORATE_ACTION_REVIEW');return result
    status,reasons=eligibility(snapshot,cfg,now)
    if status:result.status=status;result.reasons+=reasons;return result
    if not halt or halt.status!='CLEAR' or not 0<=(now-halt.checked_at).total_seconds()<=300:
        result.status='REVIEW_REQUIRED';result.reasons.append('HALT_NOT_VERIFIED_CLEAR');return result
    if mode=='PRECLOSE_ONLY' and now<bounds[1]-timedelta(minutes=20):
        result.status='MARKET_NOT_CONFIRMED';result.reasons.append('RESEARCH_WATCH_WAITING_FOR_PRECLOSE_CONFIRMATION');return result
    if mode=='CONFIRMED_EARLY_OR_DEFERRED_HALF' and change>.02 and now<bounds[1]-timedelta(minutes=20):
        result.status='MARKET_NOT_CONFIRMED';result.reasons.append('CONTINUING_PUMP_WAIT_FOR_CONFIRMATION');return result
    if not executable_short(borrow):result.status='REVIEW_REQUIRED';result.reasons.append('CURRENT_BORROW_NOT_EXECUTABLE');return result
    result.status='QUALIFIED';result.signal_side='SHORT';result.reasons+=['RANKED_FIRM_EXHAUSTION_SHORT',event['source_policy']]
    if snapshot.monthly_return<(cfg.surge_return_min_pct or 0):result.reasons.append('NOT_YET_PUMPED_OR_BELOW_PREFERRED_SURGE')
    elif cfg.ipo_low_priority_surge_max_pct is not None and snapshot.monthly_return<=cfg.ipo_low_priority_surge_max_pct:result.reasons.append('LOW_PRIORITY_MONTHLY_SURGE')
    scale=.5 if mode in {'FIRST_SIGNAL_UPMOVE_HALF_SIZE','CONFIRMED_EARLY_OR_DEFERRED_HALF'} and change>.02 else 1.
    result.ranking_evidence['ranked_firm'].update(event=event,position_scale=scale,
        position_target=policy.get('position_target',50000),decision_equity_cap=.30,decision_price_buffer=1.2)
    from .exposure import range_fraction,POLICY
    result.ranking_evidence['exposure']={'policy_id':POLICY['id'],
        'observed_range':range_fraction(history[-POLICY['range_lookback_sessions']:]),
        'basis':'Completed prior-session candles; no closing fill or future outcome'}
    result.rank=[min(m['priority'] for m in result.matches),-len(result.matches),-score]
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--collect-only',action='store_true');parser.add_argument('--preflight',action='store_true');parser.add_argument('--send',action='store_true');args=parser.parse_args()
    if args.preflight and args.send:parser.error('Preflight cannot send messages')
    root=Path.cwd();now=datetime.now(UTC);spec=json.loads((root/'config/ranked_firm_alerts.json').read_text())
    active=valid_policy(spec,root,now)
    if not active and not (args.preflight and spec.get('enabled')):print('RANKED_FIRM_POLICY_NOT_ACTIVE');return
    cfg,entries=settings(root);entities=EntityList(entries);http=Http();backend=None;path=root/'runtime/state.sqlite'
    if os.environ.get('GITHUB_ACTIONS')=='true':
        backend=GitHubState(http,required_env('GITHUB_REPOSITORY'),required_env('GITHUB_TOKEN'),cfg.state_branch);backend.restore(path)
    store=Store(path);checkpoint=backend.checkpoint if backend else lambda _:None
    try:
        digest=hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        prior_contract=store.get('ranked_contract:'+spec['id'])
        if prior_contract and prior_contract['sha256']!=digest:raise ValueError('RANKED_POLICY_CHANGED; publish a new version')
        if not prior_contract and not args.preflight:store.put('ranked_contract:'+spec['id'],{'sha256':digest,'spec':spec,'registered_at':now.isoformat()})
        candidates=[Candidate.model_validate(v) for _,v in store.items('candidate:FIRM_WATCH:')]
        cache,requests=daily_history(store,http,[c.ticker for c in candidates],now)
        if args.collect_only:print(json.dumps({'status':'RANKED_PRICES_COLLECTED','through':cache['through'],'requests':requests}));return
        previous=[str(d.date()) for d in calendar(now.year).sessions_in_range(now.date()-timedelta(days=70),now.date()-timedelta(days=1))][-22:]
        histories={};raw_histories={}
        for c in candidates:
            series=cache['split'].get(c.ticker,{});raw=cache['raw'].get(c.ticker,{})
            if len(previous)==22 and all(d in series and d in raw for d in previous):
                histories[c.ticker]=[{**series[d],'date':d} for d in previous];raw_histories[c.ticker]=[{**raw[d],'date':d} for d in previous]
        if args.prepare:
            scores=[]
            for c in candidates:
                history=histories.get(c.ticker);x=feature_row(history) if history else None
                if x is not None and raw_histories[c.ticker][-1]['c']>3:scores.append((predict(spec['model'],[{'x':x}])[0],c.ticker))
            preferred=[t for _,t in sorted(scores,reverse=True)];context=store.get('broad_discovery',{}) or {}
            context['firm_shortlist_symbols']=preferred;store.put('broad_discovery',context)
            print(json.dumps({'prepared_firms':len(preferred),'daily_requests':requests}));return
        bounds=session_bounds(now.date())
        if not bounds or not bounds[0]+timedelta(minutes=90)<=now<bounds[1]:print('RANKED_MARKET_WINDOW_CLOSED');return
        structural=[c for c in candidates if c.ticker in histories and association_structure(c,cfg,entities,now).status=='STRUCTURAL_MATCH']
        symbols=[c.ticker for c in structural];client=Bars('runtime/ranked-minute-bars',max_requests=16)
        raw=client.get(symbols,bounds[0],now-timedelta(minutes=16),'raw');split=client.get(symbols,bounds[0],now-timedelta(minutes=16),'split')
        caps=NasdaqMarketCaps(http);results=[]
        for c in structural:
            asset=store.latest_observation('market_borrow',c.ticker);borrow=(asset or {}).get('value')
            if asset and not 0<=(now-datetime.fromisoformat(asset['observed_at'])).total_seconds()<=300:borrow=None
            halted=store.latest_observation('halt_status',c.ticker)
            halt=HaltCheck(checked_at=datetime.fromisoformat(halted['observed_at']),status=halted['value'].get('status','UNKNOWN'),
                          reason='Archived live halt indication',source_url=halted['source']) if halted else None
            observed_now=datetime.now(UTC)
            result=eligible_signal(c,histories[c.ticker],raw_histories[c.ticker],partial_bar(split.get(c.ticker,[]),bounds[0],now-timedelta(minutes=16)),
                partial_bar(raw.get(c.ticker,[]),bounds[0],now-timedelta(minutes=16)),observed_now,cfg,entities,spec,borrow,halt,caps)
            sentiment=store.latest_observation('sentiment',c.ticker)
            if sentiment:result.ranking_evidence['sentiment']=sentiment
            finra=store.latest_observation('finra_short_volume',c.ticker)
            if finra:result.ranking_evidence['finra_short_volume']=finra
            reference=spec.get('drop_probability_reference')
            learned=store.get('drop_probability_live',{})
            if learned.get('context')==adaptive_context(spec):reference=learned['reference']
            if result.status=='QUALIFIED':
                result.ranking_evidence['drop_probability']=estimate(reference,result.ranking_evidence['ranked_firm']['rank_score'])
            # Base eligibility and the original model are unchanged. Adaptive
            # decisions are recorded before any additional promoted rank filter.
            if not args.preflight:result=apply_active(store,result,spec,observed_now)
            store.put('ranked_evaluation:'+c.key,result.model_dump(mode='json'));results.append(result)
            context=result.ranking_evidence.get('ranked_firm')
            if context and not args.preflight:
                phase='QUALIFIED' if result.status=='QUALIFIED' else 'WATCH'
                key='ranked_observation:'+spec['id']+':'+str(now.date())+':'+c.ticker+':'+phase
                if not store.get(key):
                    store.put(key,{'contract_id':spec['id'],'contract_sha256':digest,'ticker':c.ticker,'cik':c.cik,
                        'signal_date':str(now.date()),'entry_date':str(now.date()),'observed_at':observed_now.isoformat(),
                        'data_cutoff':(now-timedelta(minutes=16)).isoformat(),'x':context['features'],
                        'history_dates':context['feature_dates'],'paper_eligible':result.status=='QUALIFIED',
                        'feature_basis':'PROVIDER_DAILY_COMPLETED_BEFORE_ENTRY','qualification':result.status,
                        'reasons':result.reasons,'rank_score':context['rank_score']})
        folder=root/'reports';folder.mkdir(exist_ok=True)
        output={'policy_id':spec['id'],'asof':now.isoformat(),'results':[r.model_dump(mode='json') for r in results],
                'daily_requests':requests,'intraday_requests':client.requests,'orders_placed':0}
        if args.send and os.environ.get('DISCORD_ENABLED')=='true' and datetime.now(UTC)<bounds[1]:
            webhook=required_env('DISCORD_WEBHOOK_URL')
            output['delivery']=DiscordSender(http,webhook,store,checkpoint).send_new(results,cfg)
            watches=[r for r in results if r.snapshot and r.status!='QUALIFIED' and any(x in r.reasons for x in
                ('RESEARCH_WATCH_WAITING_FOR_PRECLOSE_CONFIRMATION','CONTINUING_PUMP_WAIT_FOR_CONFIRMATION','CURRENT_BORROW_NOT_EXECUTABLE'))]
            for result in sorted(watches,key=lambda r:r.rank or [0])[:3]:
                key='ranked_watch_receipt:'+spec['id']+':'+str(now.date())+':'+result.candidate.ticker
                if store.get(key):continue
                snapshot=result.snapshot;receipt={'status':'CLAIMED','at':datetime.now(UTC).isoformat()}
                store.put(key,receipt);checkpoint(store)
                from .trade_card import embed
                payload={'username':'Dudebot','content':'','allowed_mentions':{'parse':[]},
                         'embeds':[embed(result,datetime.now(UTC))]}
                try:
                    reply=http.json(webhook,method='POST',params={'wait':'true'},body=payload,timeout=8)
                    receipt.update(status='SENT',message_id=reply['id'])
                except Exception:receipt['status']='DELIVERY_UNCERTAIN'
                store.put(key,receipt);checkpoint(store)
        (folder/'ranked-firm-alerts.json').write_text(json.dumps(output,indent=2));print(json.dumps({k:v for k,v in output.items() if k!='results'}))
    finally:checkpoint(store)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        import sys
        print('ERROR: '+str(exc) if isinstance(exc,(ValueError,RuntimeError)) else 'ERROR: '+type(exc).__name__,file=sys.stderr);sys.exit(1)
