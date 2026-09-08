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
    (folder/'discord-preview.txt').write_text('\n\n--- NEXT MESSAGE ---\n\n'.join(p['content'] for p in chunks) or 'No qualified alerts. See latest.json for review and configuration reasons.')
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
    parser.add_argument('command',choices=['doctor','discover','scan','noon','demo'])
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
        if args.command=='discover':
            sec=Sec(http,required_env('SEC_USER_AGENT'),store)
            discovery=Discovery(sec,LocalParser(entries),store,cfg);candidates=discovery.run(now)
            print(json.dumps({'stored_candidates':len(candidates),'issues':discovery.issues,'filing_downloads':discovery.downloads}));return
        market=Alpaca(http,required_env('ALPACA_API_KEY'),required_env('ALPACA_SECRET_KEY'),cfg.market_feed,cfg.market_data_delay_minutes)
        candidates=[Candidate.model_validate(raw) for _,raw in store.items('candidate:')]
        candidates=[c for c in candidates if c.pipeline=='RECENT_IPO' or c.event_date>=now.date()-timedelta(days=cfg.direct_offering_backfill_days)]
        scanner=Scanner(market,NasdaqHalts(http),cfg,entities,store)
        if args.command=='noon':
            local=local_time(now,cfg);target=local.replace(hour=12,minute=0,second=0,microsecond=0).astimezone(UTC)
            # Fail closed rather than silently waiting for tomorrow when a run is late.
            if now>=target+timedelta(seconds=cfg.send_window_seconds):
                print('MISSED_SEND_WINDOW');return
            if (target-now).total_seconds()>20*60:
                print('TOO_EARLY_FOR_NOON_WORKER');return
            # Workflows start early. Prep data near noon, then refresh recent bars and halts at dispatch.
            while datetime.now(UTC)<target-timedelta(seconds=100):time.sleep(min(20,max(.1,(target-timedelta(seconds=100)-datetime.now(UTC)).total_seconds())))
        results=scanner.scan(candidates,datetime.now(UTC))
        if args.command=='noon':
            while datetime.now(UTC)<target:time.sleep(min(5,max(.02,(target-datetime.now(UTC)).total_seconds())))
            if not send_allowed(datetime.now(UTC),cfg):print('MISSED_SEND_WINDOW');report(root,results,datetime.now(UTC),cfg);return
            # Re-fetch today's price/volume for previously structurally eligible names. Fresh feed cached <=60s.
            active=[r.candidate for r in results if r.status not in {'EXCLUDED','REVIEW_REQUIRED'} or (r.snapshot is not None)]
            refreshed=scanner.scan(active,datetime.now(UTC))
            lookup={r.candidate.key:r for r in refreshed}
            results=[lookup.get(r.candidate.key,r) for r in results]
            if args.send:
                if os.environ.get('DISCORD_ENABLED')=='true':
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
