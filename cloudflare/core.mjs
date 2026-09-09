// Small hosted dispatcher: research and Alpaca downloads stay in the Python job.
export function pacificParts(time) {
  return Object.fromEntries(new Intl.DateTimeFormat('en-US', {timeZone:'America/Los_Angeles',
    year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',
    weekday:'short',hourCycle:'h23'}).formatToParts(new Date(time)).map(p=>[p.type,p.value]));
}
export function dateKey(time) {const p=pacificParts(time);return `${p.year}-${p.month}-${p.day}`;}
export function nextPacificNoon(now) {
  const start=new Date(now);start.setUTCHours(0,0,0,0);
  for(let day=0;day<8;day++)for(const hour of [19,20]) {
    const target=start.getTime()+day*86400_000+hour*3600_000,p=pacificParts(target);
    if(target>now && p.hour==='12' && !['Sat','Sun'].includes(p.weekday))return target;
  }
  throw new Error('No next Pacific noon');
}
export class ClockControl {
  constructor(storage,daily,clock=()=>Date.now()){Object.assign(this,{storage,daily,clock});}
  async state(){return await this.storage.get('control')||{paused:false,revision:0};}
  async pause() {
    await this.storage.transaction(async tx=>{
      const control=await tx.get('control')||{revision:0};
      await tx.put('control',{paused:true,revision:control.revision+1});
      await tx.put('clock',{...await tx.get('clock'),enabled:false,paused:true});
      await tx.deleteAlarm();
    });
    // The day keeps its receipt: pause/resume must never erase duplicate protection.
    await this.daily(dateKey(this.clock()),'pause');
    return {status:'PAUSED',control:await this.state(),clock:await this.storage.get('clock')};
  }
  async arm(resume=false) {
    if(resume)await this.daily(dateKey(this.clock()),'resume');
    return this.storage.transaction(async tx=>{
      const control=await tx.get('control')||{paused:false,revision:0};
      if(control.paused && !resume)return await tx.get('clock');
      const next=nextPacificNoon(this.clock()),refresh=Math.max(this.clock()+1000,next-120_000);
      const state={paused:false,revision:control.revision+1};
      const clock={enabled:true,paused:false,revision:state.revision,phase:'prepare',send_at:new Date(next).toISOString(),next_at:new Date(refresh).toISOString()};
      await tx.put('control',state);await tx.put('clock',clock);await tx.setAlarm(refresh);return clock;
    });
  }
  async active(clock) {
    const control=await this.state();return !control.paused && control.revision===(clock.revision||0);
  }
  async advance(expected,next) {
    return this.storage.transaction(async tx=>{
      const control=await tx.get('control')||{paused:false,revision:0},current=await tx.get('clock');
      if(control.paused || control.revision!==(expected.revision||0) || current?.next_at!==expected.next_at || current?.phase!==expected.phase)return false;
      await tx.put('clock',next);await tx.setAlarm(Date.parse(next.next_at));return true;
    });
  }
}
export function statusPayload(status,now) {
  const reason={NO_PREPARED_REPORT:'The data preparation job did not provide a fresh report before noon.',
    NO_QUALIFIED_MATCHES:'The prepared report contained no stocks with all required checks verified.',
    SUPPRESSED_STALE_OR_INVALID:'The prepared report failed its freshness or validation checks.'}[status];
  check(reason,'Unsupported daily status');
  return {content:'',allowed_mentions:{parse:[]},embeds:[{title:'Dudebot · Noon status',color:0xe5a92a,
    description:reason+' No stock recommendations are included in this status message.',
    fields:[{name:'Screen',value:'Listed firms first · Nasdaq/NYSE · Price > $3 · Market cap ≥ $25M'},
      {name:'Delivery',value:'Hosted noon Pacific / 2 p.m. Central status. Market data preparation may still be delayed.'}],
    footer:{text:'Dudebot · '+dateKey(now)},timestamp:new Date(now).toISOString()}]};
}
function check(value, message) {if(!value) throw new Error(message);}
function stamp(value) {check(typeof value==='string' && /(?:Z|[+-]\d\d:\d\d)$/.test(value),'Invalid timestamp'); const n=Date.parse(value);check(Number.isFinite(n),'Invalid timestamp');return n;}
export function validatePayload(p, allowPing=false) {
  check(p && typeof p==='object' && typeof p.content==='string' && p.content.length<=2000,'Invalid payload');
  check(p.allowed_mentions && JSON.stringify(p.allowed_mentions.parse)===(allowPing?'["everyone"]':'[]'),'Invalid mentions');
  check(Object.keys(p.allowed_mentions).length===1,'Unexpected mentions');
  check(Array.isArray(p.embeds) && p.embeds.length>=1 && p.embeds.length<=10,'Invalid embeds');
  let size=0;
  for(const e of p.embeds) {
    check(typeof e.title==='string' && e.title.length<=256 && typeof e.description==='string' && e.description.length<=4096,'Invalid embed text');
    size+=e.title.length+e.description.length+(e.footer?.text?.length||0);
    check((e.footer?.text?.length||0)<=2048 && (!e.fields || e.fields.length<=25),'Invalid embed fields');
    for(const f of e.fields||[]) {check(typeof f.name==='string' && f.name.length<=256 && typeof f.value==='string' && f.value.length>0 && f.value.length<=1024,'Invalid field');size+=f.name.length+f.value.length;}
  }
  check(size<=6000,'Embed too large');
}
export function validateBundle(b, now, preparing=false) {
  const target=stamp(b.send_at),p=pacificParts(target);
  check(p.hour==='12' && p.minute==='00' && p.second==='00' && !['Sat','Sun'].includes(p.weekday),'Not Pacific weekday noon');
  check(dateKey(now)===dateKey(target),'Wrong delivery date');
  check(preparing ? target-now>0 && target-now<=5*60_000 : now>=target && now<target+60_000,'Outside delivery window');
  const generated=stamp(b.generated_at);
  check(now>=generated && now-generated<=5*60_000,'Stale bundle');
  check(b.version===2 && b.profile==='firm_first' && b.feed==='sip' && b.delay_minutes===16,'Unsupported screen/data mode');
  check(Array.isArray(b.items) && b.items.length<=30,'Invalid item count');
  b.items.forEach((item,i)=>{
    check(item.status==='QUALIFIED' && item.halt_status==='CLEAR','Unqualified item');
    check(typeof item.ticker==='string' && /^[A-Z][A-Z0-9.-]*$/.test(item.ticker) && !/^[A-Z]{5}$/.test(item.ticker),'Excluded ticker');
    check(item.is_acquisition_corp===false && item.classification_evidence===true && ['XNAS','NASDAQ','XNYS','NYSE'].includes(item.exchange),'Excluded/unknown issuer');
    check(Number.isFinite(item.price) && item.price>3 && Number.isFinite(item.market_cap) && item.market_cap>=25_000_000,'Game price/capitalization exclusion');
    const capAge=now-stamp(item.market_cap_observed_at);
    check(capAge>=0 && capAge<=26*3600_000 && typeof item.market_cap_source==='string' && item.market_cap_source.startsWith('https://'),'Unknown market cap source');
    check(['CS','ADRC','ADS','COMMON_STOCK'].includes(item.security_type) && item.firm_matches>0 && item.corporate_action_review===false,'Unreviewed security/firm');
    const freshnessAt=preparing?target:now;
    for(const value of [item.price_time,item.asof]) {const time=stamp(value),age=freshnessAt-16*60_000-time;check(age>=0 && age<=300_000 && time<=now-16*60_000,'Stale/future market data');}
    const haltTime=stamp(item.halt_checked_at),haltAge=freshnessAt-haltTime;check(haltTime<=now && haltAge>=0 && haltAge<=300_000,'Stale halt check');
    const reviewTime=stamp(item.reviewed_at),reviewAge=freshnessAt-reviewTime;check(reviewTime<=now && reviewAge>=0 && reviewAge<=26*3600_000,'Stale filing review');
    validatePayload(item.payload,i===0);
  });
  return target;
}
export function webhookURL(raw) {
  const u=new URL(raw);
  check(u.protocol==='https:' && ['discord.com','discordapp.com'].includes(u.hostname) && !u.username && !u.password && !u.search && !u.hash && /^\/api(?:\/v\d+)?\/webhooks\/\d+\/[A-Za-z0-9_.-]+$/.test(u.pathname),'Invalid webhook configuration');
  return u.toString();
}
export class DispatchService {
  constructor(storage,env,request=(...args)=>fetch(...args),clock=()=>Date.now(),deliveryAllowed=async()=>true) {Object.assign(this,{storage,env,request,clock,deliveryAllowed});}
  async allowed() {
    try {return await this.deliveryAllowed() && !await this.storage.get('paused');}catch{return false;}
  }
  async pause() {
    await this.storage.transaction(async tx=>{await tx.put('paused',true);await tx.delete('bundle');await tx.deleteAlarm();});
    return {status:'PAUSED'};
  }
  async resume() {await this.storage.put('paused',false);return {status:'RESUMED',receipt:await this.storage.get('receipt')||null};}
  async prepare(bundle) {
    if(!await this.allowed())return {status:'PAUSED'};
    const target=validateBundle(bundle,this.clock(),true);
    return this.storage.transaction(async tx=>{
      if(await tx.get('paused'))return {status:'PAUSED'};
      const receipt=await tx.get('receipt'); if(receipt)return receipt;
      await tx.put('bundle',bundle);await tx.setAlarm(target);
      return {status:'ARMED',send_at:bundle.send_at,stocks:bundle.items.length};
    });
  }
  async dailyStatus(status) {
    const receipt={status,claimed_at:new Date(this.clock()).toISOString(),messages:[]};
    if(!await this.claim(receipt))return;
    try {
      if(!await this.allowed()){receipt.delivery_status='PAUSED';await this.storage.put('receipt',receipt);return receipt;}
      const payload=statusPayload(status,this.clock());validatePayload(payload,false);
      const response=await this.request(webhookURL(this.env.DISCORD_WEBHOOK_URL)+'?wait=true',{
        method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:AbortSignal.timeout(8000),redirect:'manual'});
      if(!response.ok){receipt.delivery_status='REJECTED';receipt.http_status=response.status;}
      else {const data=await response.json();check(/^\d+$/.test(data.id),'Missing status receipt');receipt.delivery_status='SENT';receipt.messages.push(data.id);}
    } catch {receipt.delivery_status='UNCERTAIN';}
    await this.storage.put('receipt',receipt);return receipt;
  }
  async claim(receipt) {
    if(!await this.allowed())return false;
    return this.storage.transaction(async tx=>{
      if(await tx.get('paused') || await tx.get('receipt'))return false;
      await tx.put('receipt',receipt);return true;
    });
  }
  async alarm(clockTick=false) {
    if(!await this.allowed())return {status:'PAUSED'};
    const bundle=await this.storage.get('bundle');
    if(await this.storage.get('receipt'))return;
    if(!bundle) {
      if(clockTick)return this.dailyStatus('NO_PREPARED_REPORT');
      return;
    }
    let receipt={status:'CLAIMED',claimed_at:new Date(this.clock()).toISOString(),messages:[]};
    try {validateBundle(bundle,this.clock());webhookURL(this.env.DISCORD_WEBHOOK_URL);}
    catch {
      const p=pacificParts(this.clock());
      if(p.hour==='12' && p.minute==='00' && !['Sat','Sun'].includes(p.weekday))return this.dailyStatus('SUPPRESSED_STALE_OR_INVALID');
      await this.claim({status:'SUPPRESSED_STALE_OR_INVALID',checked_at:receipt.claimed_at});return;
    }
    if(!bundle.items.length)return this.dailyStatus('NO_QUALIFIED_MATCHES');
    // Commit before any request; an alarm retry must not duplicate a Discord ping.
    if(!await this.claim(receipt))return;
    for(const item of bundle.items) {
      try {
        if(!await this.allowed()){receipt.status='PAUSED';break;}
        validateBundle(bundle,this.clock());
        const response=await this.request(webhookURL(this.env.DISCORD_WEBHOOK_URL)+'?wait=true',{
          method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(item.payload),signal:AbortSignal.timeout(8000),redirect:'manual'});
        if(!response.ok){receipt.status=response.status===429?'RATE_LIMITED':'DISCORD_REJECTED';receipt.http_status=response.status;break;}
        const data=await response.json();check(/^\d+$/.test(data.id),'Missing Discord receipt');
        receipt.messages.push(data.id);receipt.status=receipt.messages.length===bundle.items.length?'SENT':'PARTIAL';
      } catch {receipt.status='DELIVERY_UNCERTAIN';break;}
      finally {await this.storage.put('receipt',receipt);}
    }
    await this.storage.put('receipt',receipt);
  }
}
