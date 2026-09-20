"""Point-in-time Alpaca asset and borrow evidence.

`borrow_status` is the only borrow field retained. Alpaca deprecated
`easy_to_borrow`; archiving it would make the dataset stop working when that
field disappears and would lose the distinction between unavailable states.
"""
BORROW_AVAILABLE={'easy_to_borrow'}

def current_assets(http,symbols,headers=None,base='https://paper-api.alpaca.markets'):
    assets={}
    for s in symbols:
        try:
            x=http.json(base+'/v2/assets/'+s,headers={**(headers or {}),'Accept':'application/json'})
            assets[s]={k:x.get(k) for k in ('symbol','name','exchange','asset_class','tradable','shortable','borrow_status')}
            assets[s]['asset_status']=x.get('status')
            assets[s]['borrow_available']=bool(x.get('shortable') and x.get('borrow_status') in BORROW_AVAILABLE)
            assets[s].update(status='CURRENT',source=base+'/v2/assets/'+s)
        except Exception as e:assets[s]={'status':'UNAVAILABLE','error_type':type(e).__name__}
    return {'assets':assets,'historical_status':'ARCHIVED_OBSERVATIONS_ONLY','limitation':'Borrow is known only at archived observation times and does not prove SMG Security Table membership.'}

def executable_short(asset):
    return bool(asset and asset.get('status')=='CURRENT' and asset.get('tradable') and
                asset.get('shortable') and asset.get('borrow_status') in BORROW_AVAILABLE)
