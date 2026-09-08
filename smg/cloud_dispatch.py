"""Prepare real evaluated alerts for the free Cloudflare noon dispatcher."""
import hashlib,json,os,time
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.parse import urlsplit
from .notify import digest

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
            asof=s.asof.isoformat(),price_time=s.price_time.isoformat(),payload=payload))
    if len(items)>30:raise ValueError('More than 30 qualified stocks: dispatcher capacity review required')
    return dict(version=1,profile='firm_first',feed='sip',delay_minutes=16,generated_at=now.isoformat(),send_at=target.isoformat(),items=items)

def prepare(http,endpoint,webhook,results,now,target,cfg):
    body=bundle(results,now,target,cfg)
    result=http.json(endpoint_url(endpoint)+'/prepare',method='POST',headers={'Authorization':'Bearer '+dispatch_key(webhook)},body=body)
    if result.get('status')!='ARMED':raise ValueError('Cloudflare did not arm a new delivery; inspect dispatcher status')
    return result

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
            if health.get('version')==1 and health.get('configured') is True:break
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
    if formatted.get('status')!='UPDATED' or formatted.get('message_id')!=receipt['message_id']:raise ValueError('Cloudflare Discord smoke check failed')
    record=dict(enabled=True,endpoint=endpoint,verified_at=now.isoformat(),practice_edit=formatted,
                limitation='Hosted delivery verified; first real noon alarm and qualified delivery still pending')
    store.put('cloud_dispatch',record);backend.checkpoint(store)
    folder=root/'reports';folder.mkdir(exist_ok=True)
    (folder/'cloudflare-deployment.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))

if __name__=='__main__':register()
