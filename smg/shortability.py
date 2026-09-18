"""Current Alpaca borrow evidence; historical availability remains unknown."""
def current_assets(http,symbols,base='https://api.alpaca.markets',api_key=None,secret_key=None):
    assets={}
    for s in symbols:
        try:
            headers={'Accept':'application/json'}
            if api_key and secret_key:headers.update({'APCA-API-KEY-ID':api_key,'APCA-API-SECRET-KEY':secret_key})
            x=http.json(base+'/v2/assets/'+s,headers=headers)
            assets[s]={k:x.get(k) for k in ('symbol','tradable','shortable','borrow_status','easy_to_borrow')}
            assets[s].update(status='CURRENT',source=base+'/v2/assets/'+s)
        except Exception as e:assets[s]={'status':'UNAVAILABLE','error_type':type(e).__name__}
    return {'assets':assets,'historical_status':'UNAVAILABLE','limitation':'Current borrow status cannot prove historical availability or SMG Security Table membership.'}

def archive_current(store,http,symbols,now,api_key,secret_key):
    day=now.date().isoformat();result=current_assets(http,symbols,api_key=api_key,secret_key=secret_key)
    for symbol,row in result['assets'].items():
        key=f'borrow_archive:{day}:{symbol}'
        if store.get(key) is None:store.put(key,dict(observed_at=now.isoformat(),**row))
    store.put('borrow_archive:last_run',dict(observed_at=now.isoformat(),symbols=len(symbols),historical_status='UNAVAILABLE'))
    return result
