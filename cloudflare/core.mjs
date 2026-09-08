// Small hosted dispatcher: research and Alpaca downloads stay in the Python job.
export function pacificParts(time) {
  return Object.fromEntries(new Intl.DateTimeFormat('en-US', {timeZone:'America/Los_Angeles',
    year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',
    weekday:'short',hourCycle:'h23'}).formatToParts(new Date(time)).map(p=>[p.type,p.value]));
}
export function dateKey(time) {const p=pacificParts(time);return `${p.year}-${p.month}-${p.day}`;}
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
  constructor(storage,env,request=fetch,clock=Date.now) {Object.assign(this,{storage,env,request,clock});}
  async prepare(bundle) {
    const target=validateBundle(bundle,this.clock(),true);
    return this.storage.transaction(async tx=>{
      const receipt=await tx.get('receipt'); if(receipt)return receipt;
      await tx.put('bundle',bundle);await tx.setAlarm(target);
      return {status:'ARMED',send_at:bundle.send_at,stocks:bundle.items.length};
    });
  }
  async alarm() {
    const bundle=await this.storage.get('bundle');
    if(!bundle || await this.storage.get('receipt'))return;
    let receipt={status:'CLAIMED',claimed_at:new Date(this.clock()).toISOString(),messages:[]};
    try {validateBundle(bundle,this.clock());webhookURL(this.env.DISCORD_WEBHOOK_URL);}
    catch {await this.storage.put('receipt',{status:'SUPPRESSED_STALE_OR_INVALID',checked_at:receipt.claimed_at});return;}
    // Commit before any request; an alarm retry must not duplicate a Discord ping.
    await this.storage.put('receipt',receipt);
    if(!bundle.items.length){receipt.status='NO_QUALIFIED_MATCHES';await this.storage.put('receipt',receipt);return;}
    for(const item of bundle.items) {
      try {
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
