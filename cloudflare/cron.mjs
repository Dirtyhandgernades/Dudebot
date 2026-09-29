const WORKFLOW='https://api.github.com/repos/Dirtyhandgernades/Dudebot/actions/workflows/evidence-archive.yml/dispatches';

export async function dispatchScan(env,request=fetch) {
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
