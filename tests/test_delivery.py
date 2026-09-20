from datetime import datetime,timedelta,timezone
from pathlib import Path
import yaml
from smg.notify import send_allowed,local_time,DiscordSender,digest,clean
from smg.models import Config
from smg.demo import NOW,run_demo
from smg.rules import EntityList
from smg.storage import Store
from smg.transport import ProviderError
UTC=timezone.utc
URL='https://discord.com/api/webhooks/123456/not-a-real-token'

def demo():return run_demo(Config(),EntityList(yaml.safe_load(Path('config/entities.yaml').read_text())))[0]

class FakeHttp:
    def __init__(self,fail=False):self.calls=[];self.fail=fail
    def json(self,url,**kw):
        self.calls.append(kw)
        if self.fail:raise ProviderError('discord.com')
        return {'id':str(len(self.calls))}

def test_noon_only_and_literal_pst():
    cfg=Config()
    assert send_allowed(NOW,cfg)
    for dt in [NOW-timedelta(hours=1),NOW-timedelta(minutes=1),NOW+timedelta(minutes=1),NOW.replace(day=7)]:assert not send_allowed(dt,cfg)
    assert local_time(NOW,cfg).hour==12
    assert local_time(NOW,cfg.model_copy(update={'notification_timezone':'America/Los_Angeles'})).hour==13

def test_one_ping_and_payload_limits():
    p=digest(demo(),NOW,Config())
    assert p[0]['content'].startswith('@everyone\n')
    assert all(len(x['content'])<=2000 for x in p)
    assert all(x['allowed_mentions']['parse']==[] for x in p[1:])
    assert '@everyone' not in clean('@everyone <@123>')
    for message in p:
        e=message['embeds'][0]
        assert len(e['title'])<=256 and len(e['description'])<=4096
        assert all(len(f['value'])<=1024 for f in e['fields'])
        assert len(e['title'])+len(e['description'])+len(e['footer']['text'])+sum(len(f['name'])+len(f['value']) for f in e['fields'])<=6000

def test_claim_persisted_before_send_and_dedup(tmp_path):
    store=Store(tmp_path/'s.db');http=FakeHttp();checkpoints=[]
    sender=DiscordSender(http,URL,store,lambda s:checkpoints.append(s.get('delivery:2026-09-08')['status']),clock=lambda:NOW)
    assert sender.send(demo(),Config())=='SENT'
    count=len(http.calls);assert checkpoints[0]=='CLAIMED'
    assert sender.send(demo(),Config())=='ALREADY_CLAIMED' and len(http.calls)==count

def test_uncertain_delivery_no_retry(tmp_path):
    store=Store(tmp_path/'s.db');http=FakeHttp(fail=True)
    sender=DiscordSender(http,URL,store,lambda s:None,clock=lambda:NOW)
    assert sender.send(demo(),Config())=='DELIVERY_UNCERTAIN'
    assert sender.send(demo(),Config())=='ALREADY_CLAIMED' and len(http.calls)==1

def test_event_delivery_sends_new_phase_once_without_noon_gate(tmp_path):
    store=Store(tmp_path/'s.db');http=FakeHttp();checkpoints=[]
    at=NOW-timedelta(minutes=30)  # 11:30 Pacific: old noon sender would reject it.
    items=demo()
    for e in items:
        if e.snapshot:
            e.snapshot.asof=at;e.snapshot.price_time=at-timedelta(minutes=1)
            e.snapshot.market_cap_observed_at=at
        if e.halt:e.halt.checked_at=at
    sender=DiscordSender(http,URL,store,lambda s:checkpoints.append(True),clock=lambda:at)
    first=sender.send_new(items,Config())
    assert first['status']=='SENT' and first['new_trades']>=1
    calls=len(http.calls)
    assert sender.send_new(items,Config())=='NO_NEW_TRADES' and len(http.calls)==calls
    assert checkpoints and http.calls[0]['body']['content'].startswith('@everyone')

def test_two_discovery_lanes_do_not_duplicate_same_ticker_trade(tmp_path):
    store=Store(tmp_path/'s.db');http=FakeHttp();items=[e for e in demo() if e.status=='QUALIFIED'][:1]
    duplicate=items[0].model_copy(deep=True);duplicate.candidate.pipeline='VOLATILITY_WATCH';duplicate.candidate.event_id='VOLATILITY'
    duplicate.reasons=['NO_LISTED_FIRM_MATCH','PUMP_FAILURE_SHORT'];duplicate.matches=[];duplicate.rank=[1,9,0,-5,-10,-2,-30]
    sender=DiscordSender(http,URL,store,lambda s:None,clock=lambda:NOW)
    result=sender.send_new(items+[duplicate],Config())
    assert result['new_trades']==1 and len(http.calls)==1

def test_late_claim_does_not_send(tmp_path):
    store=Store(tmp_path/'s.db');http=FakeHttp();times=iter([NOW,NOW+timedelta(minutes=1)])
    sender=DiscordSender(http,URL,store,lambda s:None,clock=lambda:next(times))
    assert sender.send(demo(),Config())=='MISSED_WINDOW' and not http.calls

def test_changed_halt_and_stale_result_suppressed(tmp_path):
    store=Store(tmp_path/'s.db');http=FakeHttp();items=demo()
    for item in items:
        if item.halt:item.halt.status='HALTED'
    sender=DiscordSender(http,URL,store,lambda s:None,clock=lambda:NOW)
    assert sender.send(items,Config())=='NO_QUALIFIED_MATCHES' and not http.calls

def test_practice_reformat_edits_same_message_without_second_post(tmp_path):
    store=Store(tmp_path/'s.db');http=FakeHttp()
    sender=DiscordSender(http,URL,store,lambda s:None,clock=lambda:NOW)
    first=sender.activation('practice','Practice')
    body={'content':'','embeds':[{'title':'Practice','description':'Current research only'}]}
    updated=sender.activation('practice',body,format_version='embed-v1')
    assert updated['message_id']==first['message_id'] and updated['format_status']=='UPDATED'
    assert [c['method'] for c in http.calls]==['POST','PATCH']
    assert http.calls[-1]['body']['allowed_mentions']=={'parse':[]}
    sender.activation('practice',body,format_version='embed-v1')
    assert len(http.calls)==2
