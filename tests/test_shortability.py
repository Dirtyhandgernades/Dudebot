from smg.shortability import current_assets
class HTTP:
    def json(self,url,**kwargs):return {'symbol':'ABC','tradable':True,'shortable':True,'borrow_status':'easy_to_borrow','easy_to_borrow':True}
def test_current_borrow_fields_and_historical_gap():
    x=current_assets(HTTP(),['ABC']);assert x['assets']['ABC']['borrow_status']=='easy_to_borrow';assert x['historical_status']=='UNAVAILABLE'
