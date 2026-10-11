const WORKFLOW='https://api.github.com/repos/Dirtyhandgernades/Dudebot/actions/workflows/evidence-archive.yml/dispatches';

export async function dispatchScan(env,request=fetch,scheduledTime=Date.now()) {
  const parts=Object.fromEntries(new Intl.DateTimeFormat('en-US',{
    timeZone:'America/New_York',weekday:'short',hour:'2-digit',minute:'2-digit',hourCycle:'h23',
  }).formatToParts(new Date(scheduledTime)).map(p=>[p.type,p.value]));
  if(['Sat','Sun'].includes(parts.weekday))return {status:'WEEKEND_SKIPPED'};
  const minute=Number(parts.hour)*60+Number(parts.minute);
  // Preparation before the open and delayed closing-bar collection are useful.
  // Python's exchange calendar still enforces holidays and actual trade windows.
  if(minute<9*60 || minute>16*60+30)return {status:'OUTSIDE_SCAN_WINDOW'};
  if(!env.GITHUB_WORKFLOW_TOKEN)return {status:'TOKEN_NOT_CONFIGURED'};
  const response=await request(WORKFLOW,{
    method:'POST',
    headers:{'Authorization':'Bearer '+env.GITHUB_WORKFLOW_TOKEN,
      'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28',
      'User-Agent':'Dudebot-Cloudflare-Scheduler','Content-Type':'application/json'},
    body:JSON.stringify({ref:'main',inputs:{mode:'current'}}),
    redirect:'manual',signal:AbortSignal.timeout(8000),
  });
  if(response.status!==204)throw new Error('GitHub workflow dispatch HTTP '+response.status);
  return {status:'DISPATCHED'};
}
