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
