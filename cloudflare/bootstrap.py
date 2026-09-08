"""Register the free workers.dev address only when this account has none."""
import os
import requests

account=os.environ['CLOUDFLARE_ACCOUNT_ID']
url=f'https://api.cloudflare.com/client/v4/accounts/{account}/workers/subdomain'
headers={'Authorization':'Bearer '+os.environ['CLOUDFLARE_API_TOKEN']}
response=requests.get(url,headers=headers,timeout=20)
data=response.json()
existing=(data.get('result') or {}).get('subdomain')
if response.ok and data.get('success') and existing:
    print('Existing workers.dev address retained: '+existing+'.workers.dev')
else:
    codes={e.get('code') for e in data.get('errors',[])}
    if not (response.status_code==404 or codes=={10007} or (response.ok and data.get('success') and not existing)):
        raise SystemExit('Cloudflare address lookup failed: HTTP '+str(response.status_code)+'; codes '+str(sorted(codes)))
    chosen='dudebot-dirtyhandgernades'
    response=requests.put(url,headers=headers,json={'subdomain':chosen},timeout=20)
    data=response.json()
    if not response.ok or not data.get('success'):
        raise SystemExit('Cloudflare free address registration failed: HTTP '+str(response.status_code)+'; complete Workers onboarding in the dashboard')
    print('Registered free address: '+chosen+'.workers.dev')
