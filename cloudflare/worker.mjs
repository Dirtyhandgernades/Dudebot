import {DurableObject} from 'cloudflare:workers';
import {DispatchService,dateKey,pacificParts,nextPacificNoon,validatePayload,webhookURL} from './core.mjs';

async function authorized(request,env) {
  if(!env.DISPATCH_KEY || env.DISPATCH_KEY.length!==64)return false;
  const supplied=request.headers.get('Authorization')||'';
  const encoder=new TextEncoder();
  const a=new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode(supplied)));
  const b=new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode('Bearer '+env.DISPATCH_KEY)));
  let delta=0;for(let i=0;i<a.length;i++)delta|=a[i]^b[i];return delta===0;
}
export default {
  async fetch(request,env) {
    const path=new URL(request.url).pathname;
    if(path==='/health' && request.method==='GET')return Response.json({service:'dudebot-dispatch',version:2,configured:!!env.DISPATCH_KEY && !!env.DISCORD_WEBHOOK_URL});
    if(!await authorized(request,env))return Response.json({error:'Unauthorized'},{status:401});
    if(path==='/clock' && ['GET','POST'].includes(request.method))return env.DISPATCH.getByName('persistent-noon-clock').fetch(request);
    if(request.method==='GET' && path==='/status')return env.DISPATCH.getByName(dateKey(Date.now())).fetch(request);
    if(request.method!=='POST' || !['/prepare','/practice-format','/verify'].includes(path))return new Response('Not found',{status:404});
    let stage='read';
    try {
      const raw=await request.text();if(raw.length>200_000)return new Response('Too large',{status:413});
      const body=JSON.parse(raw);
      if(path==='/practice-format') {
        stage='validate_practice';
        if(!/^\d+$/.test(body.message_id))throw new Error('Invalid message');
        validatePayload(body.payload,false);
        const destination=webhookURL(env.DISCORD_WEBHOOK_URL)+'/messages/'+body.message_id;
        stage='discord_edit';
        const response=await fetch(destination,{
          method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(body.payload),signal:AbortSignal.timeout(8000),redirect:'manual'});
        if(!response.ok)return Response.json({status:'EDIT_FAILED',http_status:response.status},{status:502});
        stage='discord_receipt';
        const data=await response.json();return Response.json({status:'UPDATED',message_id:data.id});
      }
      return env.DISPATCH.getByName(dateKey(Date.now())).fetch(new Request(request.url,{method:'POST',body:raw}));
    } catch(e) {return Response.json({status:'FORMAT_FAILED',error:'Invalid request or delivery failed',stage,error_type:e.name},{status:path==='/practice-format'?200:400});}
  }
};
export class NoonDispatch extends DurableObject {
  constructor(ctx,env){super(ctx,env);this.service=new DispatchService(ctx.storage,env);}
  async fetch(request) {
    const path=new URL(request.url).pathname;
    if(path==='/clock') {
      if(request.method==='POST') {
        const next=nextPacificNoon(Date.now());
        await this.ctx.storage.put('clock',{enabled:true,next_at:new Date(next).toISOString()});
        await this.ctx.storage.setAlarm(next);
      }
      return Response.json({clock:await this.ctx.storage.get('clock')||null,last:await this.ctx.storage.get('clock_last')||null});
    }
    if(path==='/clock-tick') {
      const p=pacificParts(Date.now());
      if(p.hour!=='12'||p.minute!=='00'||['Sat','Sun'].includes(p.weekday))return Response.json({status:'OUTSIDE_NOON_WINDOW'});
      await this.service.alarm(true);
      return Response.json({receipt:await this.ctx.storage.get('receipt')||null});
    }
    if(request.method==='GET')return Response.json({receipt:await this.ctx.storage.get('receipt')||null,verification:await this.ctx.storage.get('verification')||null,armed:!!await this.ctx.storage.get('bundle')});
    if(path==='/verify') {
      // Verify durable persistence without modifying an armed noon alarm.
      await this.ctx.storage.put('verification',{status:'VERIFIED',at:new Date().toISOString()});
      return Response.json({status:'VERIFIED'});
    }
    try {return Response.json(await this.service.prepare(await request.json()));}
    catch {return Response.json({error:'Bundle validation failed'},{status:400});}
  }
  async alarm(){
    const clock=await this.ctx.storage.get('clock');
    if(!clock?.enabled)return this.service.alarm();
    const due=Date.parse(clock.next_at),now=Date.now();
    // Schedule tomorrow before dispatch so a provider failure cannot stop the clock.
    const next=nextPacificNoon(Math.max(now,due));
    await this.ctx.storage.put('clock',{...clock,next_at:new Date(next).toISOString()});
    await this.ctx.storage.setAlarm(next);
    if(now<due || now-due>=60_000) {
      await this.ctx.storage.put('clock_last',{status:'MISSED_CLOCK_WINDOW',due_at:clock.next_at});return;
    }
    try {
      const response=await this.env.DISPATCH.getByName(dateKey(now)).fetch(new Request('https://internal/clock-tick',{method:'POST'}));
      await this.ctx.storage.put('clock_last',await response.json());
    } catch {await this.ctx.storage.put('clock_last',{status:'DISPATCH_UNCERTAIN'});}
  }
}
