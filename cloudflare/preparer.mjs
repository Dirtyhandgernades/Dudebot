import {validateBundle} from './core.mjs';

function requireValue(value,message){if(!value)throw new Error(message);}
export function validateSeed(seed,now) {
  requireValue(seed?.version===1 && Array.isArray(seed.candidates) && seed.candidates.length<=30,'Invalid seed');
  requireValue(Number.isFinite(Date.parse(seed.generated_at)) && Date.parse(seed.generated_at)<=now,'Invalid seed time');
  for(const c of seed.candidates) {
    requireValue(/^[A-Z][A-Z0-9.-]*$/.test(c.ticker) && !/^[A-Z]{5}$/.test(c.ticker),'Invalid ticker');
    requireValue(c.is_acquisition_corp===false && c.classification_evidence===true && c.corporate_action_review===false,'Unverified issuer');
    requireValue(['CS','ADRC','ADS','COMMON_STOCK'].includes(c.security_type) && ['XNAS','XNYS','NASDAQ','NYSE'].includes(c.exchange),'Invalid security');
    requireValue(Number.isFinite(Date.parse(c.reviewed_at)) && Date.parse(c.reviewed_at)<=now,'Invalid source review');
    requireValue(Array.isArray(c.firms) && c.firms.length>0 && c.firms.every(f=>typeof f.name==='string' && f.name.length<=200 && ['auditor','underwriter','counsel'].includes(f.role)),'Invalid firms');
    requireValue(typeof c.source_url==='string' && c.source_url.startsWith('https://www.sec.gov/Archives/edgar/'),'Invalid source');
  }
  return seed;
}
function plain(s){return s.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g,'$1').replace(/<[^>]*>/g,'').trim();}
export function haltedSymbols(xml,now) {
  requireValue(/<rss\b/.test(xml) && /<channel\b/.test(xml),'Invalid halt feed');
  const halted=new Set();
  for(const match of xml.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/g)) {
    const fields={};
    for(const f of match[1].matchAll(/<(?:[\w-]+:)?([\w-]+)\b[^>]*>([\s\S]*?)<\/(?:[\w-]+:)?\1>/g))fields[f[1].toLowerCase()]=plain(f[2]);
    const symbol=fields.issuesymbol||fields.symbol;requireValue(symbol,'Missing halt symbol');
    const day=/^(\d{2})\/(\d{2})\/(\d{4})$/.exec(fields.resumptiondate||'');
    const time=/^(\d{2}):(\d{2}):(\d{2})$/.exec(fields.resumptiontradetime||'');
    let resumed=false;
    if(day && time) {
      const noon=Date.UTC(+day[3],+day[1]-1,+day[2],12);
      const zone=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',timeZoneName:'shortOffset'}).formatToParts(noon).find(p=>p.type==='timeZoneName').value;
      const offset=Number(/GMT([+-]\d+)/.exec(zone)?.[1]);
      if(Number.isFinite(offset))resumed=Date.UTC(+day[3],+day[1]-1,+day[2],+time[1]-offset,+time[2],+time[3])<=now;
    }
    if(!resumed)halted.add(symbol.toUpperCase());
  }
  return halted;
}
export class HostedPreparer {
  constructor(env,request=fetch,clock=Date.now){Object.assign(this,{env,request,clock});}
  async get(url,headers={}) {
    const r=await this.request(url,{headers,redirect:'manual',signal:AbortSignal.timeout(10000)});
    requireValue(r.ok,new URL(url).hostname+' HTTP '+r.status);return r;
  }
  async prepare(seed,target,verifyOnly=false) {
    const now=this.clock();validateSeed(seed,now);
    requireValue(this.env.ALPACA_API_KEY && this.env.ALPACA_SECRET_KEY,'Missing Alpaca connection');
    const candidates=seed.candidates.filter(c=>target-Date.parse(c.reviewed_at)>=0 && target-Date.parse(c.reviewed_at)<=26*3600_000);
    const capSources={};const capValues={};
    for(const exchange of ['nasdaq','nyse']) {
      const url='https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=0&exchange='+exchange;
      const r=await this.get(url,{'User-Agent':'Mozilla/5.0','Accept':'application/json','Origin':'https://www.nasdaq.com'});
      const data=await r.json(),rows=data?.data?.table?.rows;requireValue(Array.isArray(rows),'Invalid cap feed');
      for(const row of rows) {const cap=Number(String(row.marketCap||'').replaceAll(',',''));if(cap>0){capValues[row.symbol]=cap;capSources[row.symbol]=url;}}
    }
    const capTime=new Date(this.clock()).toISOString();
    const haltResponse=await this.get('https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts');
    const haltTime=this.clock(),headerTime=Date.parse(haltResponse.headers.get('Date'));
    requireValue(Number.isFinite(headerTime) && haltTime-headerTime>=-60_000 && haltTime-headerTime<=300_000 && Number(haltResponse.headers.get('Age')||0)<=60,'Stale halt feed');
    const halted=haltedSymbols(await haltResponse.text(),haltTime);
    const effective=Math.floor(this.clock()/60_000)*60_000-16*60_000;
    let bars={};
    {
      // SPY is an API access probe only when the watch is empty; it is never added to candidates.
      const query=new URLSearchParams({symbols:candidates.length?candidates.map(c=>c.ticker).join(','):'SPY',timeframe:'1Min',start:new Date(effective-5*60_000).toISOString(),
        end:new Date(effective-60_000).toISOString(),feed:'sip',adjustment:'raw',limit:'10000'});
      const response=await this.get('https://data.alpaca.markets/v2/stocks/bars?'+query,{'APCA-API-KEY-ID':this.env.ALPACA_API_KEY,'APCA-API-SECRET-KEY':this.env.ALPACA_SECRET_KEY});
      const data=await response.json();requireValue(!data.next_page_token,'Incomplete price response');bars=data.bars||{};
    }
    const items=[];
    for(const c of candidates) {
      const rows=(bars[c.ticker]||[]).filter(r=>Date.parse(r.t)<=effective-60_000).sort((a,b)=>Date.parse(a.t)-Date.parse(b.t));
      const last=rows.at(-1),cap=capValues[c.ticker];
      if(!last || !(last.c>3) || !(cap>=25_000_000) || halted.has(c.ticker))continue;
      const age=target-16*60_000-Date.parse(last.t);if(age<0 || age>300_000)continue;
      const fields=[{name:'Listed firms',value:c.firms.map(f=>f.name+' ('+f.role+')').join('\n').slice(0,1024)},
        {name:'Price / game eligibility',value:'$'+last.c.toFixed(2)+' · Reported cap $'+(cap/1e6).toFixed(1)+'M\nMinimum 10 shares: $'+(last.c*10).toFixed(2)+' before fees'},
        {name:'Filing evidence',value:c.source_url},{name:'Pump / volume context',value:'Monthly surge and relative volume unavailable in hosted refresh; these remain preferences.'}];
      const payload={content:items.length?'':'@everyone',allowed_mentions:{parse:items.length?[]:['everyone']},embeds:[{title:c.ticker+' · FIRM-FIRST WATCH',color:0x26a69a,
        description:'Listed-firm research watch. Fresh delayed price and required eligibility checks passed. Firm association does not establish misconduct or predict a fall.',
        fields,footer:{text:'Free SIP delayed 16 minutes · Cap is a current vendor report, without a published valuation timestamp'},timestamp:new Date(target).toISOString()}]};
      items.push({...c,status:'QUALIFIED',firm_matches:c.firms.length,price:last.c,market_cap:cap,market_cap_observed_at:capTime,market_cap_source:capSources[c.ticker],
        halt_status:'CLEAR',halt_checked_at:new Date(haltTime).toISOString(),asof:new Date(effective).toISOString(),price_time:last.t,payload});
    }
    const bundle={version:2,profile:'firm_first',feed:'sip',delay_minutes:16,generated_at:new Date(this.clock()).toISOString(),send_at:new Date(target).toISOString(),items};
    if(!verifyOnly)validateBundle(bundle,this.clock(),true);
    return {bundle,audit:{seed_candidates:seed.candidates.length,fresh_source_candidates:candidates.length,qualified:items.length,provider_check:'VERIFIED',at:new Date(this.clock()).toISOString()}};
  }
}
