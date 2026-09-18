"""Current Alpaca borrow evidence; historical availability remains unknown."""
def current_assets(http,symbols,base='https://api.alpaca.markets'):
    assets={}
    for s in symbols:
        try:
            x=http.json(base+'/v2/assets/'+s,headers={'Accept':'application/json'})
            assets[s]={k:x.get(k) for k in ('symbol','tradable','shortable','borrow_status','easy_to_borrow')}
            assets[s].update(status='CURRENT',source=base+'/v2/assets/'+s)
        except Exception as e:assets[s]={'status':'UNAVAILABLE','error_type':type(e).__name__}
    return {'assets':assets,'historical_status':'UNAVAILABLE','limitation':'Current borrow status cannot prove historical availability or SMG Security Table membership.'}
