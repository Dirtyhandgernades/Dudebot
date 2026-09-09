import test from 'node:test';
import assert from 'node:assert/strict';
import {HostedPreparer,haltedSymbols,validateSeed} from './preparer.mjs';
const target=Date.parse('2026-09-09T19:00:00Z'),now=target-120_000;
const candidate={ticker:'TEST',is_acquisition_corp:false,classification_evidence:true,corporate_action_review:false,
  security_type:'CS',exchange:'XNAS',reviewed_at:new Date(target-3600_000).toISOString(),
  firms:[{name:'Listed auditor',role:'auditor'}],source_url:'https://www.sec.gov/Archives/edgar/data/1/report.htm'};
const seed=()=>({version:1,generated_at:new Date(now-60_000).toISOString(),candidates:[structuredClone(candidate)]});
const emptyRSS='<rss><channel></channel></rss>';
function provider({price=4,cap=25_000_000,rss=emptyRSS,stamp=now}={}) {
  return async(url,options)=>{
    if(url.includes('api.nasdaq.com'))return Response.json({data:{table:{rows:[{symbol:'TEST',marketCap:String(cap)}]}}});
    if(url.includes('nasdaqtrader'))return new Response(rss,{headers:{Date:new Date(stamp).toUTCString()}});
    assert.match(url,/feed=sip/);assert.equal(options.headers['APCA-API-KEY-ID'],'fake');
    return Response.json({bars:{TEST:[{t:new Date(now-17*60_000).toISOString(),c:price}]}});
  };
}
const env={ALPACA_API_KEY:'fake',ALPACA_SECRET_KEY:'fake'};
test('hosted refresh uses real provider fields and same hard bundle validation',async()=>{
  const result=await new HostedPreparer(env,provider(),()=>now).prepare(seed(),target);
  assert.equal(result.bundle.items.length,1);assert.equal(result.bundle.items[0].price,4);
  assert.equal(result.bundle.items[0].market_cap,25_000_000);assert.equal(result.audit.provider_check,'VERIFIED');
  assert.deepEqual(result.audit.decisions,[{ticker:'TEST',status:'QUALIFIED',reasons:[],price:4,market_cap:25_000_000}]);
});
test('price, capitalization and stale filing reviews cannot produce hosted stock picks',async()=>{
  for(const options of [{price:3},{cap:24_999_999}])assert.equal((await new HostedPreparer(env,provider(options),()=>now).prepare(seed(),target)).bundle.items.length,0);
  const stale=seed();stale.candidates[0].reviewed_at=new Date(now-27*3600_000).toISOString();
  assert.equal((await new HostedPreparer(env,provider(),()=>now).prepare(stale,target)).bundle.items.length,0);
  const invalid=seed();invalid.candidates[0].ticker='ABCDE';assert.throws(()=>validateSeed(invalid,now));
});
test('preparation audit separates hard exclusions from unavailable data',async()=>{
  const result=await new HostedPreparer(env,provider({price:3,cap:0}),()=>now).prepare(seed(),target);
  assert.deepEqual(result.audit.decisions[0].reasons,['PRICE_NOT_ABOVE_3','MARKET_CAP_UNAVAILABLE']);
  const stale=seed();stale.candidates[0].reviewed_at=new Date(now-27*3600_000).toISOString();
  assert.deepEqual((await new HostedPreparer(env,provider(),()=>now).prepare(stale,target)).audit.decisions[0].reasons,['STALE_SOURCE_REVIEW']);
});
test('unhealthy halt feed fails preparation and halted symbols are withheld',async()=>{
  await assert.rejects(new HostedPreparer(env,provider({stamp:now-3600_000}),()=>now).prepare(seed(),target),/Stale halt/);
  const rss='<rss><channel><item><ndaq:IssueSymbol>TEST</ndaq:IssueSymbol></item></channel></rss>';
  assert.equal((await new HostedPreparer(env,provider({rss}),()=>now).prepare(seed(),target)).bundle.items.length,0);
});
test('halt resumption must have occurred, using New York local time',()=>{
  const item=time=>'<item><ndaq:IssueSymbol>TEST</ndaq:IssueSymbol><ndaq:ResumptionDate>09/09/2026</ndaq:ResumptionDate><ndaq:ResumptionTradeTime>'+time+'</ndaq:ResumptionTradeTime></item>';
  assert.equal(haltedSymbols('<rss><channel>'+item('14:00:00')+'</channel></rss>',now).size,0);
  assert.equal(haltedSymbols('<rss><channel>'+item('15:00:00')+'</channel></rss>',now).has('TEST'),true);
});
