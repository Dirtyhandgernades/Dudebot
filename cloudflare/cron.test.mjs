import test from 'node:test';
import assert from 'node:assert/strict';
import {dispatchScan} from './cron.mjs';
const FRIDAY=Date.parse('2026-10-09T19:45:00Z');

test('hosted cron stays inert without a dedicated GitHub token',async()=>{
  assert.deepEqual(await dispatchScan({},()=>{throw Error('unexpected request');},FRIDAY),{status:'TOKEN_NOT_CONFIGURED'});
});

test('hosted cron dispatches only the current scan workflow',async()=>{
  let called=false;
  const result=await dispatchScan({GITHUB_WORKFLOW_TOKEN:'test-token'},async(url,options)=>{
    called=true;
    assert.equal(url,'https://api.github.com/repos/Dirtyhandgernades/Dudebot/actions/workflows/evidence-archive.yml/dispatches');
    assert.equal(options.method,'POST');
    assert.deepEqual(JSON.parse(options.body),{ref:'main',inputs:{mode:'current'}});
    return {status:204};
  },FRIDAY);
  assert(called);assert.deepEqual(result,{status:'DISPATCHED'});
});

test('hosted cron exposes a rejected GitHub dispatch',async()=>{
  await assert.rejects(dispatchScan({GITHUB_WORKFLOW_TOKEN:'invalid'},async()=>({status:401}),FRIDAY),/HTTP 401/);
});

test('weekends and out-of-window stale cron invocations never dispatch',async()=>{
  for(const at of ['2026-10-10T19:45:00Z','2026-10-11T19:45:00Z'])
    assert.deepEqual(await dispatchScan({},()=>{throw Error('unexpected');},Date.parse(at)),{status:'WEEKEND_SKIPPED'});
  for(const at of ['2026-10-09T12:45:00Z','2026-10-09T20:45:00Z','2026-11-06T13:45:00Z','2026-11-06T21:45:00Z'])
    assert.deepEqual(await dispatchScan({},()=>{throw Error('unexpected');},Date.parse(at)),{status:'OUTSIDE_SCAN_WINDOW'});
});

test('Friday dispatch remains open across daylight saving and delayed close collection',async()=>{
  for(const at of ['2026-10-09T13:00:00Z','2026-10-09T20:30:00Z','2026-11-06T14:00:00Z','2026-11-06T21:30:00Z'])
    assert.deepEqual(await dispatchScan({GITHUB_WORKFLOW_TOKEN:'fixture'},async()=>({status:204}),Date.parse(at)),{status:'DISPATCHED'});
});
