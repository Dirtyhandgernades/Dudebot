import test from 'node:test';
import assert from 'node:assert/strict';
import {dispatchScan} from './cron.mjs';

test('hosted cron stays inert without a dedicated GitHub token',async()=>{
  assert.deepEqual(await dispatchScan({},()=>{throw Error('unexpected request');}),{status:'TOKEN_NOT_CONFIGURED'});
});

test('hosted cron dispatches only the current scan workflow',async()=>{
  let called=false;
  const result=await dispatchScan({GITHUB_WORKFLOW_TOKEN:'test-token'},async(url,options)=>{
    called=true;
    assert.equal(url,'https://api.github.com/repos/Dirtyhandgernades/Dudebot/actions/workflows/evidence-archive.yml/dispatches');
    assert.equal(options.method,'POST');
    assert.deepEqual(JSON.parse(options.body),{ref:'main',inputs:{mode:'current'}});
    return {status:204};
  });
  assert(called);assert.deepEqual(result,{status:'DISPATCHED'});
});

test('hosted cron exposes a rejected GitHub dispatch',async()=>{
  await assert.rejects(dispatchScan({GITHUB_WORKFLOW_TOKEN:'invalid'},async()=>({status:401})),/HTTP 401/);
});
