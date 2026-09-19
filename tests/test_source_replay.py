import json,sqlite3
from bs4 import BeautifulSoup
from smg.source_replay import select_sources,source_identity
from lxml import html as lhtml

def test_source_selection_uses_dated_firm_corpus_and_distinct_issuers(tmp_path):
    path=tmp_path/'sources.sqlite';db=sqlite3.connect(path)
    db.execute('CREATE TABLE hits (id TEXT, source TEXT)')
    for key,cik,form,day in [('a','1','20-F','2024-04-01'),('b','1','8-K','2024-04-02'),('c','2','20-F','2024-05-01'),('future','3','20-F','2026-04-01')]:
        db.execute('INSERT INTO hits VALUES (?,?)',(key,json.dumps(dict(ciks=[cik],form=form,file_date=day))))
    db.commit();db.close()
    assert [i for i,_ in select_sources(path,per_quarter=6)]==['a','c']
    assert [i for i,_ in select_sources(path)]==['a','c','b']


def test_primary_documents_and_pre_window_baseline_are_selected(tmp_path):
    path=tmp_path/'sources.sqlite';db=sqlite3.connect(path)
    db.execute('CREATE TABLE hits (id TEXT, source TEXT)')
    for key,kind in [('main','20-F'),('consent','EX-15.1')]:
        db.execute('INSERT INTO hits VALUES (?,?)',(key,json.dumps(dict(ciks=['1'],form='20-F',file_type=kind,file_date='2022-04-01'))))
    db.commit();db.close()
    assert [i for i,_ in select_sources(path)]==['main']


def test_registered_symbol_overrides_historical_prose_symbol():
    raw='''<ix:nonNumeric name="dei:TradingSymbol">NEW</ix:nonNumeric>
    <ix:nonNumeric name="dei:SecurityExchangeName">NASDAQ</ix:nonNumeric>
    <p>Our previous ticker symbol "OLD".</p>'''
    soup=BeautifulSoup(raw,'html.parser')
    assert source_identity(soup,soup.get_text(' ',strip=True))[:2]==('NEW','XNAS')
    native=lhtml.document_fromstring(raw)
    assert source_identity(native,' '.join(native.itertext()))[:2]==('NEW','XNAS')


def test_registration_table_maps_common_equity_without_using_warrant_ticker():
    raw='''<table><tr><td>Title of each class</td><td>Trading Symbol(s)</td><td>Name of exchange</td></tr>
    <tr><td>Ordinary shares</td><td>ABCD (1)</td><td>Nasdaq Capital Market</td></tr>
    <tr><td>Warrants</td><td>ABCDW</td><td>Nasdaq Capital Market</td></tr></table>'''
    soup=BeautifulSoup(raw,'html.parser')
    assert source_identity(soup,soup.get_text(' ',strip=True))[:2]==('ABCD','XNAS')
    native=lhtml.document_fromstring(raw)
    assert source_identity(native,' '.join(native.itertext()))[:2]==('ABCD','XNAS')


def test_other_company_ticker_cannot_become_the_issuer_identity():
    raw='<p>We are a private advertising company. A former employer was Expedia (NASDAQ:EXPE). Companies may be listed on Nasdaq.</p>'
    native=lhtml.document_fromstring(raw)
    assert source_identity(native,' '.join(native.itertext()))[:2]==(None,None)
    raw='<p>Our ordinary shares are listed on the Nasdaq Capital Market under the symbol "REAL". Expedia (NASDAQ:EXPE) is a customer.</p>'
    native=lhtml.document_fromstring(raw)
    assert source_identity(native,' '.join(native.itertext()))[:2]==('REAL','XNAS')


def test_nyse_american_is_not_treated_as_nyse():
    raw='<table><tr><td>Trading Symbol(s)</td></tr><tr><td>Common stock</td><td>TEST</td><td>NYSE American</td></tr></table>'
    native=lhtml.document_fromstring(raw)
    assert source_identity(native,' '.join(native.itertext()))[:2]==(None,None)


def test_unit_and_warrant_rows_do_not_override_common_equity():
    raw = """<table><tr><td>Trading Symbol(s)</td></tr>
    <tr><td>Units, each consisting of one common stock share</td><td>SWAGU</td><td>The NASDAQ Stock Market LLC</td></tr>
    <tr><td>Common <span>Stock</span></td><td>SWAG</td><td>The NASDAQ Stock Market LLC</td></tr>
    <tr><td>Warrants, each exercisable for common stock</td><td>SWAGW</td><td>The NASDAQ Stock Market LLC</td></tr></table>"""
    for soup in (BeautifulSoup(raw,'html.parser'),lhtml.document_fromstring(raw)):
        assert source_identity(soup,'')[:2]==('SWAG','XNAS')


def test_full_inline_exchange_name_and_invisible_whitespace():
    raw = '<ix:nonNumeric name="dei:TradingSymbol"> ABCD </ix:nonNumeric><ix:nonNumeric name="dei:SecurityExchangeName">The NASDAQ Stock Market LLC</ix:nonNumeric>'
    assert source_identity(lhtml.document_fromstring(raw),'')[:2]==('ABCD','XNAS')
    raw=raw.replace('The NASDAQ Stock Market LLC','NYSE American')
    assert source_identity(lhtml.document_fromstring(raw),'')[:2]==(None,None)


def test_strict_transactions_extracted_from_dated_source_without_labels():
    from smg.source_replay import parse_source
    from datetime import date
    raw = '<p>This is an initial public offering. We are offering 1,000,000 ordinary shares at a price of $5 per share. Our ordinary shares are listed on Nasdaq under the symbol "ABCD".</p>'
    strict=[]
    parse_source('0000000001-24-000001:filing.htm',{'ciks':['1'],'file_date':'2024-06-01'},raw,{},strict)
    assert len(strict)==1
    assert strict[0].pipeline=='RECENT_IPO'
    assert strict[0].ticker=='ABCD'
    assert strict[0].reviewed_at.date()>date(2024,6,1)
