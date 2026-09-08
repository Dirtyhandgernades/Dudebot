import test from 'node:test';
import assert from 'node:assert/strict';
import {dateKey,pacificParts,validateBundle,DispatchService} from './core.mjs';
const target=Date.parse('2026-09-08T19:00:00Z');
function fixture() {
  return {version:2,profile:'firm_first',feed:'sip',delay_minutes:16,send_at:new Date(target).toISOString(),generated_at:new Date(target-90_000).toISOString(),
    items:[{status:'QUALIFIED',ticker:'TEST',is_acquisition_corp:false,classification_evidence:true,exchange:'XNAS',security_type:'CS',firm_matches:1,
      corporate_action_review:false,halt_status:'CLEAR',halt_checked_at:new Date(target-90_000).toISOString(),reviewed_at:new Date(target-3600_000).toISOString(),
      price:4,market_cap:25_000_000,market_cap_observed_at:new Date(target-3600_000).toISOString(),market_cap_source:'https://example.com/fixture',
      asof:new Date(target-18*60_000).toISOString(),price_time:new Date(target-18*60_000).toISOString(),
      payload:{content:'@everyone\nResearch watchlist',allowed_mentions:{parse:['everyone']},embeds:[{title:'TEST',description:'Test fixture',fields:[]}]}}]};
}
class Storage {
  records=new Map(); alarmTime=null;
  async get(k){return structuredClone(this.records.get(k));}
  async put(k,v){this.records.set(k,structuredClone(v));}
  async setAlarm(t){this.alarmTime=t;}
  async transaction(fn){return fn(this);}
}
test('Pacific noon follows both seasons',()=>{
  assert.equal(pacificParts(target).hour,'12');
  assert.equal(pacificParts(Date.parse('2026-01-15T20:00:00Z')).hour,'12');
  assert.equal(dateKey(target),'2026-09-08');
  const wrong=fixture();wrong.send_at='2026-09-08T20:00:00Z';assert.throws(()=>validateBundle(wrong,target-90_000,true));
});
test('hard exclusions and stale data suppress delivery',()=>{
  for(const change of [{ticker:'ABCDE'},{is_acquisition_corp:true},{classification_evidence:false},{halt_status:'UNKNOWN'},
    {price:3},{market_cap:24_999_999},{market_cap:null},{corporate_action_review:true},{firm_matches:0},{halt_checked_at:'2026-09-08T18:00:00Z'},{price_time:'2026-09-08T18:00:00Z'}]) {
    const b=fixture();Object.assign(b.items[0],change);assert.throws(()=>validateBundle(b,target));
  }
  assert.throws(()=>validateBundle(fixture(),target+60_000));
  assert.equal(validateBundle(fixture(),target),target);
});
test('claim is persisted before Discord and an alarm retry does not resend',async()=>{
  const storage=new Storage();let clock=target-90_000,calls=0;
  const service=new DispatchService(storage,{DISCORD_WEBHOOK_URL:'https://discord.com/api/webhooks/123/fake'},async()=>{
    assert.equal((await storage.get('receipt')).status,'CLAIMED');calls++;return Response.json({id:'12345'});
  },()=>clock);
  assert.equal((await service.prepare(fixture())).status,'ARMED');assert.equal(storage.alarmTime,target);
  clock=target;await service.alarm();await service.alarm();
  assert.equal(calls,1);assert.equal((await storage.get('receipt')).status,'SENT');
});
test('ambiguous delivery is not automatically retried',async()=>{
  const storage=new Storage();let clock=target-90_000,calls=0;
  const service=new DispatchService(storage,{DISCORD_WEBHOOK_URL:'https://discord.com/api/webhooks/123/fake'},async()=>{calls++;throw new Error('network');},()=>clock);
  await service.prepare(fixture());clock=target;await service.alarm();await service.alarm();
  assert.equal(calls,1);assert.equal((await storage.get('receipt')).status,'DELIVERY_UNCERTAIN');
});
test('late alarm records suppression without contacting Discord',async()=>{
  const storage=new Storage();let clock=target-90_000,calls=0;
  const service=new DispatchService(storage,{},async()=>{calls++;},()=>clock);
  await service.prepare(fixture());clock=target+60_000;await service.alarm();assert.equal(calls,0);
  assert.equal((await storage.get('receipt')).status,'SUPPRESSED_STALE_OR_INVALID');
});
