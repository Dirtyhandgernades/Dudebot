from smg.shortability import current_assets,executable_short
class HTTP:
    def json(self,url,**kwargs):return {'symbol':'ABC','tradable':True,'shortable':True,'borrow_status':'easy_to_borrow','easy_to_borrow':True}
def test_current_borrow_fields_and_historical_gap():
    x=current_assets(HTTP(),['ABC'],{'APCA-API-KEY-ID':'redacted'})
    assert x['assets']['ABC']['borrow_status']=='easy_to_borrow'
    assert 'easy_to_borrow' not in x['assets']['ABC'] and executable_short(x['assets']['ABC'])
    assert x['historical_status']=='ARCHIVED_OBSERVATIONS_ONLY'

def test_hard_or_unknown_borrow_is_not_executable():
    for status in ['hard_to_borrow','not_shortable',None]:
        assert not executable_short({'status':'CURRENT','tradable':True,'shortable':True,'borrow_status':status})
