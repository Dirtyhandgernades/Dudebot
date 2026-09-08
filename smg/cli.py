import argparse,os,json,time,sys
from pathlib import Path
from datetime import datetime,timezone,timedelta
import yaml
from .models import Config,Candidate,Evaluation
from .rules import EntityList
from .transport import Http
from .storage import Store,GitHubState
from .providers import Alpaca,Sec,NasdaqHalts
from .extraction import LocalParser
from .discovery import Discovery
from .runner import Scanner
from .notify import digest,DiscordSender,local_time,send_allowed
UTC=timezone.utc

def settings(root):
    cfg=Config.model_validate(yaml.safe_load((root/'config/strategy.yaml').read_text()))
    overrides={}
    if os.environ.get('SURGE_RETURN_MIN_PCT','').strip():
        overrides['surge_return_min_pct']=os.environ['SURGE_RETURN_MIN_PCT']
    if overrides:
        cfg=Config.model_validate(dict(cfg.model_dump(),**overrides))
    entries=yaml.safe_load((root/'config/entities.yaml').read_text())
    if cfg.rvol_min_sessions>cfg.rvol_target_sessions:raise ValueError('Invalid RVOL window')
    if cfg.market_feed=='sip' and cfg.market_data_delay_minutes<16:raise ValueError('Free SIP mode requires at least 16 minutes of delay')
    return cfg,entries

def report(root,results,now,cfg,issues=()):
    folder=root/'reports';folder.mkdir(exist_ok=True)
    raw={'asof':now.isoformat(),'config':cfg.model_dump(),'issues':list(issues),'results':[r.model_dump(mode='json') for r in results]}
    (folder/'latest.json').write_text(json.dumps(raw,indent=2,allow_nan=False))
    chunks=digest(results,now,cfg)
    (folder/'discord-preview.txt').write_text('\n\n--- NEXT MESSAGE ---\n\n'.join(p['content']+'\n'+json.dumps(p.get('embeds',[]),indent=2) for p in chunks) or 'No qualified alerts. See latest.json for review and configuration reasons.')
    (folder/'discord-payloads.json').write_text(json.dumps(chunks,indent=2))
    counts={}
    for r in results:counts[r.status]=counts.get(r.status,0)+1
    print(json.dumps({'evaluations':counts,'issues':len(issues),'report':'reports/latest.json'}))

def required_env(name):
    value=os.environ.get(name,'')
    if not value:raise ValueError('Missing '+name+'; configure it as a GitHub Actions secret')
    return value

def main():
    parser=argparse.ArgumentParser(description='DECA SMG notifier (no order execution)')
    parser.add_argument('command',choices=['doctor','discover','scan','noon','demo','activate','practice'])
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--send',action='store_true',help='Only noon mode can send, and only during the configured noon minute')
    args=parser.parse_args();root=args.root.resolve();cfg,entries=settings(root)
    if args.send and args.command!='noon':parser.error('--send is available only for noon mode')
    if args.command=='demo':
        from .demo import run_demo
        results,now=run_demo(cfg,EntityList(entries));report(root,results,now,cfg,['SYNTHETIC FIXTURES: demo uses an explicit 100% threshold for demonstration only']);return
    if args.command=='doctor':
        checks={key:bool(os.environ.get(key)) for key in ['ALPACA_API_KEY','ALPACA_SECRET_KEY','SEC_USER_AGENT','DISCORD_WEBHOOK_URL']}
        print(json.dumps({'secrets_present':checks,'hosted_ai_required':False,'market_feed':cfg.market_feed,'market_data_delay_minutes':cfg.market_data_delay_minutes,'surge_threshold_configured':cfg.surge_return_min_pct is not None,'time':cfg.notification_timezone+' 12:00','sending_enabled':os.environ.get('DISCORD_ENABLED')=='true'},indent=2));return
    http=Http();backend=None;path=root/'runtime/state.sqlite'
    if os.environ.get('GITHUB_ACTIONS')=='true':
        backend=GitHubState(http,required_env('GITHUB_REPOSITORY'),required_env('GITHUB_TOKEN'),cfg.state_branch)
        backend.restore(path)
    store=Store(path)
    checkpoint=backend.checkpoint if backend else lambda state:None
    entities=EntityList(entries)
    now=datetime.now(UTC)
    try:
        if args.command=='practice':
            if os.environ.get('DISCORD_ENABLED')!='true':raise ValueError('Discord delivery is disabled')
            from .practice import practice_payload,practice_embed
            payload,audit=practice_payload(store,root,now,cfg,entities)
            sender=DiscordSender(http,required_env('DISCORD_WEBHOOK_URL'),store,checkpoint)
            payload=practice_embed(payload,audit,now)
            receipt=sender.activation('practice-reference-check-2026-09-08',payload,format_version='embed-v1')
            folder=root/'reports';folder.mkdir(exist_ok=True)
            (folder/'practice.json').write_text(json.dumps(dict(receipt=receipt,audit=audit),indent=2))
            (folder/'practice-embed.json').write_text(json.dumps(payload,indent=2))
            print(json.dumps({'practice_receipt':receipt,'overlap':audit['overlap_tickers']}));return
        if args.command=='discover':
            sec=Sec(http,required_env('SEC_USER_AGENT'),store)
            if cfg.screening_profile=='firm_first':
                from .live_firms import LiveFirmDiscovery
                discovery=LiveFirmDiscovery(sec,LocalParser(entries),store,cfg)
            else:discovery=Discovery(sec,LocalParser(entries),store,cfg)
            candidates=discovery.run(now)
            print(json.dumps({'stored_candidates':len(candidates),'issues':discovery.issues,'filing_downloads':discovery.downloads}));return
        if args.command=='activate':
            if os.environ.get('DISCORD_ENABLED')!='true':raise ValueError('Discord delivery is disabled')
            from .backtest import probe_market
            health=probe_market(cfg)
            if health.get('status')!='ACCESS_VERIFIED':raise ValueError('Alpaca health probe failed')
            discovery=store.get('live_discovery')
            if not discovery:raise ValueError('Run live discovery before activation')
            sender=DiscordSender(http,required_env('DISCORD_WEBHOOK_URL'),store,checkpoint)
            release=json.loads((root/'config/deployment.json').read_text())['release_id']
            content=('Dudebot is deployed with the firm-first screen. Underwriters, auditors and counsel lead the watchlist; stocks can qualify before a pump.\n'
                'Hard exclusions: halted/suspended stocks, SPACs/acquisition corporations, and exactly-five-letter tickers. Unknown checks suppress stock alerts.\n'
                'Stock alerts: weekdays at 12:00 Pacific / 2:00 Central, following daylight saving time, using free Alpaca SIP delayed 16 minutes. GitHub scheduling can run late.\n'
                f'Initial discovery reviewed {discovery["reviewed"]} source records; further work resumes on schedule. Coverage remains partial.\n'
                'Historical screening replay is incomplete; no detection rate is established. This is an activation receipt, not a stock alert.')
            receipt=sender.activation(release,content)
            folder=root/'reports';folder.mkdir(exist_ok=True)
            (folder/'activation.json').write_text(json.dumps(dict(receipt,provider_health=health,discovery=discovery),indent=2))
            print(json.dumps({'activation':receipt}));return
        market=Alpaca(http,required_env('ALPACA_API_KEY'),required_env('ALPACA_SECRET_KEY'),cfg.market_feed,cfg.market_data_delay_minutes)
        candidates=[Candidate.model_validate(raw) for _,raw in store.items('candidate:')]
        candidates=[c for c in candidates if c.pipeline in {'RECENT_IPO','FIRM_WATCH'} or c.event_date>=now.date()-timedelta(days=cfg.direct_offering_backfill_days)]
        scanner=Scanner(market,NasdaqHalts(http),cfg,entities,store)
        if args.command=='noon':
            local=local_time(now,cfg);target=local.replace(hour=12,minute=0,second=0,microsecond=0).astimezone(UTC)
            # Fail closed rather than silently waiting for tomorrow when a run is late.
            if now>=target+timedelta(seconds=cfg.send_window_seconds):
                print('MISSED_SEND_WINDOW');return
            if (target-now).total_seconds()>60*60:
                print('TOO_EARLY_FOR_NOON_WORKER');return
            # Workflows start early. Prep data near noon, then refresh recent bars and halts at dispatch.
            while datetime.now(UTC)<target-timedelta(seconds=480):time.sleep(min(20,max(.1,(target-timedelta(seconds=480)-datetime.now(UTC)).total_seconds())))
        results=scanner.scan(candidates,datetime.now(UTC))
        if args.command=='noon':
            refresh_at=target-timedelta(seconds=90)
            while datetime.now(UTC)<refresh_at:time.sleep(min(5,max(.02,(refresh_at-datetime.now(UTC)).total_seconds())))
            # Re-fetch today's price/volume for previously structurally eligible names. Fresh feed cached <=60s.
            active=[r.candidate for r in results if r.status not in {'EXCLUDED','REVIEW_REQUIRED'} or (r.snapshot is not None)]
            refreshed=scanner.scan(active,datetime.now(UTC))
            lookup={r.candidate.key:r for r in refreshed}
            results=[lookup.get(r.candidate.key,r) for r in results]
            if args.send:
                if os.environ.get('DISCORD_ENABLED')=='true':
                    cloud=store.get('cloud_dispatch',{})
                    if cloud.get('enabled'):
                        from .cloud_dispatch import prepare
                        key='delivery:'+str(local_time(target,cfg).date())
                        if store.get(key):print('ALREADY_CLAIMED')
                        elif datetime.now(UTC)>=target:print('MISSED_CLOUDFLARE_PREPARATION_WINDOW')
                        else:
                            # The GitHub sender and hosted sender share a single delivery claim.
                            store.put(key,{'status':'CLAIMED_BY_CLOUDFLARE','claimed_at':datetime.now(UTC).isoformat()});checkpoint(store)
                            receipt=prepare(http,cloud['endpoint'],required_env('DISCORD_WEBHOOK_URL'),results,datetime.now(UTC),target,cfg)
                            store.put('cloud_prepared:'+str(local_time(target,cfg).date()),receipt)
                            print(json.dumps(receipt))
                    else:
                        while datetime.now(UTC)<target:time.sleep(min(5,max(.02,(target-datetime.now(UTC)).total_seconds())))
                        sender=DiscordSender(http,required_env('DISCORD_WEBHOOK_URL'),store,checkpoint)
                        print(sender.send(results,cfg))
                else:print('DISCORD_DISABLED; report generated without sending')
        report(root,results,datetime.now(UTC),cfg,store.get('discovery_issues',[]))
    finally:checkpoint(store)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        # Provider errors are already credential-redacted. Never emit request headers or secret URLs.
        print('ERROR: '+str(exc) if isinstance(exc,(ValueError,RuntimeError)) else 'ERROR: '+type(exc).__name__,file=sys.stderr)
        sys.exit(1)
