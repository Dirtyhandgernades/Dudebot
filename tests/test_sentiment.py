from smg.sentiment import collect
class HTTP:
    def text(self,url,**kwargs): return '<html>short float news</html>' if 'finviz' in url else '<rss><channel><item><title>Shares surge after contract</title></item></channel></rss>'
    def json(self,url,**kwargs): return {'messages':[{'entities':{'sentiment':{'basic':'Bullish'}}}]}
def test_sentiment_is_optional_context():
    x=collect('TEST',HTTP());assert x['score'] is not None and x['providers']['finviz']['status']=='AVAILABLE'
def test_provider_failure_is_gap():
    class Broken:
        def text(self,*a,**k):raise RuntimeError()
        def json(self,*a,**k):raise RuntimeError()
    x=collect('TEST',Broken());assert x['score'] is None
