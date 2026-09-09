"""Prepare real evaluated alerts for the free Cloudflare noon dispatcher."""
import hashlib,json,os,time
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.parse import urlsplit
from .notify import digest
from .game_rules import eligibility

def dispatch_key(webhook):
    # Domain-separated derivative of the existing high-entropy secret. Never logged.
    return hashlib.sha256(('dudebot-dispatch-v1:'+webhook).encode()).hexdigest()

def endpoint_url(value):
    u=urlsplit(value.rstrip('/'))
    if u.scheme!='https' or not u.hostname or not u.hostname.endswith('.workers.dev') or u.username or u.password or u.port or u.path or u.query or u.fragment:
        raise ValueError('Expected Cloudflare workers.dev deployment origin')
    return value.rstrip('/')

def bundle(results,now,target,cfg):
    if cfg.screening_profile!='firm_first' or cfg.market_feed!='sip' or cfg.market_data_delay_minutes!=16:
        raise ValueError('Cloudflare dispatcher requires the configured firm-first free SIP profile')
    good=[]
    for e in results:
        if e.status!='QUALIFIED' or not e.snapshot or not e.halt or e.halt.status!='CLEAR':continue
        if eligibility(e.snapshot,cfg,target)[0]:continue
        s=e.snapshot;effective=target-timedelta(minutes=16)
        if s.feed!='sip' or s.declared_delay_minutes!=16:continue
        if not 0<=(target-e.halt.checked_at).total_seconds()<=300:continue
        if any(not 0<=(effective-t).total_seconds()<=300 for t in [s.asof,s.price_time]):continue
        good.append(e)
    good.sort(key=lambda e:e.rank)
    payloads=digest(good,target,cfg);items=[]
    for e,payload in zip(good,payloads):
        c=e.candidate;s=e.snapshot
        items.append(dict(status=e.status,ticker=c.ticker,is_acquisition_corp=c.is_acquisition_corp,
            classification_evidence='is_acquisition_corp' in c.evidence,exchange=c.exchange,security_type=c.security_type,
            firm_matches=len(e.matches),corporate_action_review='CORPORATE_ACTION_REVIEW' in s.flags,
            halt_status=e.halt.status,halt_checked_at=e.halt.checked_at.isoformat(),reviewed_at=c.reviewed_at.isoformat(),
            asof=s.asof.isoformat(),price_time=s.price_time.isoformat(),price=s.price,market_cap=s.market_cap,
            market_cap_observed_at=s.market_cap_observed_at.isoformat(),market_cap_source=s.market_cap_source,payload=payload))
    if len(items)>30:raise ValueError('More than 30 qualified stocks: dispatcher capacity review required')
    return dict(version=2,profile='firm_first',feed='sip',delay_minutes=16,generated_at=now.isoformat(),send_at=target.isoformat(),items=items)

def prepare(http,endpoint,webhook,results,now,target,cfg):
    body=bundle(results,now,target,cfg)
    result=http.json(endpoint_url(endpoint)+'/prepare',method='POST',headers={'Authorization':'Bearer '+dispatch_key(webhook)},body=body)
    if result.get('status')!='ARMED':raise ValueError('Cloudflare did not arm a new delivery; inspect dispatcher status')
    return result

def seed_candidates(candidates,now,cfg,entities):
    from .firm_first import firm_structure
    selected=[]
    for c in candidates:
        result=firm_structure(c,cfg,entities,now)
        if c.pipeline!='FIRM_WATCH' or result.status!='STRUCTURAL_MATCH':continue
        if any('ads ratio' in n.lower() or 'ticker change' in n.lower() for n in c.notes):continue
        selected.append((min(m['priority'] for m in result.matches),-len(result.matches),c,result))
    selected.sort(key=lambda x:(x[0],x[1],x[2].ticker))
    rows=[]
    for _,_,c,result in selected[:30]:
        rows.append(dict(ticker=c.ticker,is_acquisition_corp=False,classification_evidence=True,corporate_action_review=False,
            exchange=c.exchange,security_type=c.security_type,reviewed_at=c.reviewed_at.isoformat(),
            firms=[dict(name=m['name'],role=m['role']) for m in result.matches],source_url=c.matches[0].evidence.url))
    return dict(version=1,generated_at=now.isoformat(),candidates=rows,omitted_for_capacity=max(0,len(selected)-30))

def upload_seed(http,endpoint,webhook,candidates,now,cfg,entities):
    return http.json(endpoint_url(endpoint)+'/seed',method='POST',headers={'Authorization':'Bearer '+dispatch_key(webhook)},
                     body=seed_candidates(candidates,now,cfg,entities))

def register():
    """Deployment smoke check, then select one delivery owner in persistent state."""
    from .cli import settings,required_env
    from .transport import Http
    from .storage import Store,GitHubState
    from .rules import EntityList
    from .practice import practice_payload,practice_embed
    root=Path.cwd();cfg,entries=settings(root);http=Http()
    if os.environ.get('DISCORD_ENABLED')!='true':raise ValueError('Discord delivery is disabled')
    endpoint=endpoint_url(required_env('CLOUDFLARE_DEPLOYMENT_URL'))
    webhook=required_env('DISCORD_WEBHOOK_URL');headers={'Authorization':'Bearer '+dispatch_key(webhook)}
    from .transport import ProviderError
    for attempt in range(12):
        try:
            health=http.json(endpoint+'/health',timeout=10)
            if health.get('version')==3 and health.get('configured') is True:break
        except ProviderError:pass
        if attempt==11:raise ValueError('Cloudflare HTTPS/route is not ready; rerun deployment after propagation')
        if attempt==0:print('Waiting briefly for the new Cloudflare HTTPS endpoint to become ready')
        time.sleep(5)
    verify=http.json(endpoint+'/verify',method='POST',headers=headers,body={})
    if verify.get('status')!='VERIFIED':raise ValueError('Cloudflare durable storage verification failed')
    backend=GitHubState(http,required_env('GITHUB_REPOSITORY'),required_env('GITHUB_TOKEN'),cfg.state_branch)
    path=root/'runtime/state.sqlite';backend.restore(path);store=Store(path)
    receipt=store.get('activation:practice-reference-check-2026-09-08')
    if not receipt or receipt.get('status')!='SENT':raise ValueError('Confirmed practice message required before activating hosted delivery')
    now=datetime.now(timezone.utc)
    text,audit=practice_payload(store,root,now,cfg,EntityList(entries))
    formatted=http.json(endpoint+'/practice-format',method='POST',headers=headers,
        body={'message_id':receipt['message_id'],'payload':practice_embed(text,audit,now)})
    if formatted.get('status')!='UPDATED' or formatted.get('message_id')!=receipt['message_id']:
        raise ValueError('Cloudflare Discord smoke check failed: '+str({k:formatted.get(k) for k in ['status','stage','error_type','http_status']}))
    from .models import Candidate
    candidates=[Candidate.model_validate(raw) for _,raw in store.items('candidate:FIRM_WATCH:')]
    seed=upload_seed(http,endpoint,webhook,candidates,now,cfg,EntityList(entries))
    provider_check=http.json(endpoint+'/preparation-check',method='POST',headers=headers,body={},timeout=55)
    if provider_check.get('provider_check')!='VERIFIED':raise ValueError('Cloudflare market preparation check failed: '+str(provider_check))
    clock=http.json(endpoint+'/clock',method='POST',headers=headers,body={}).get('clock')
    if not clock or not clock.get('enabled'):raise ValueError('Hosted noon clock was not enabled')
    record=dict(enabled=True,endpoint=endpoint,verified_at=now.isoformat(),practice_edit=formatted,clock=clock,seed=seed,provider_check=provider_check,
                limitation='Hosted price/cap/halt refresh and clock enabled; first noon alarm pending. GitHub still refreshes the source-reviewed candidate pool; stale sources are withheld.')
    store.put('cloud_dispatch',record);backend.checkpoint(store)
    folder=root/'reports';folder.mkdir(exist_ok=True)
    (folder/'cloudflare-deployment.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))

if __name__=='__main__':register()
