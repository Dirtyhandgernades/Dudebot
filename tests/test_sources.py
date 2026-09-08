import pytest
from smg.providers import parse_halts
from smg.demo import NOW
from smg.extraction import LocalParser
from smg.rules import structural,EntityList
from smg.models import Config
from pathlib import Path
import yaml

XML='''<rss xmlns:ndaq="http://www.nasdaqtrader.com/"><channel><item><ndaq:IssueSymbol>ABCD</ndaq:IssueSymbol>{resume}</item></channel></rss>'''

def test_halt_resume_and_quote_only():
    assert parse_halts(XML.format(resume=''),NOW)=={'ABCD'}
    resume='<ndaq:ResumptionDate>09/08/2026</ndaq:ResumptionDate><ndaq:ResumptionTradeTime>15:00:00</ndaq:ResumptionTradeTime>'
    assert parse_halts(XML.format(resume=resume),NOW)==set()
    quote='<ndaq:ResumptionDate>09/08/2026</ndaq:ResumptionDate><ndaq:ResumptionQuoteTime>15:00:00</ndaq:ResumptionQuoteTime>'
    assert parse_halts(XML.format(resume=quote),NOW)=={'ABCD'}

def test_malformed_halt_schema_fails_closed():
    with pytest.raises(ValueError):parse_halts('<rss><channel><item><title>unknown</title></item></channel></rss>',NOW)

ENTITIES=yaml.safe_load(Path('config/entities.yaml').read_text())
IPO_TEXT="""This is our initial public offering. We are offering 4,000,000 ordinary shares.
The initial public offering price is $5.00 per ordinary share. Gross proceeds of $20 million
will be received before expenses. Dollar amounts are expressed in U.S. dollars.
Our principal operations are in China. Our ordinary shares began trading on the Nasdaq
Capital Market on July 15, 2026. Cathay Securities acts as underwriter in this offering."""


def parse(text=IPO_TEXT,pipeline='RECENT_IPO',context_docs=()):
    context={'pipeline':pipeline,'date':'2026-09-07','accession':'0000000001-26-000001',
             'ticker':'ABCD','cik':'1','name':'Synthetic Operating Company'}
    doc={'text':' '.join(text.split()),'url':'https://www.sec.gov/Archives/synthetic',
         'date':'2026-09-07','sha256':'synthetic-sha'}
    return LocalParser(ENTITIES).extract(context,[doc,*context_docs],NOW),doc


def test_local_parser_supported_ipo_has_exact_evidence():
    candidate,doc=parse()
    assert str(candidate.ipo_date)=='2026-07-15'
    assert candidate.offer_price==5 and candidate.offer_gross==20e6
    assert structural(candidate,Config(),EntityList(ENTITIES),NOW).status=='STRUCTURAL_MATCH'
    assert all(e.quote in doc['text'] for e in candidate.evidence.values())
    assert all(e.evidence.quote in doc['text'] for e in candidate.matches)


def test_missing_date_never_uses_filing_date_as_ipo_date():
    candidate,_=parse(IPO_TEXT.replace('began trading','applied to trade'))
    assert candidate.ipo_date is None
    result=structural(candidate,Config(),EntityList(ENTITIES),NOW)
    assert result.status=='REVIEW_REQUIRED' and 'MISSING_IPO_DATE' in result.reasons


def test_old_ipo_underwriter_does_not_qualify_direct_offering():
    text=IPO_TEXT.replace('This is our initial public offering.','On September 7, 2026, we entered into a securities purchase agreement for a registered direct offering.').replace('Cathay Securities acts as underwriter in this offering.','')
    old={'text':'Cathay Securities acted as underwriter of our original initial public offering.',
         'url':'https://www.sec.gov/Archives/synthetic-old','date':'2025-08-01','sha256':'old','context_only':True}
    candidate,_=parse(text,'DIRECT_OFFERING',[old])
    assert candidate.event_id=='2026-09-07'
    assert not EntityList(ENTITIES).match(candidate)


def test_direct_offering_is_separate_and_us_operations_allowed():
    text=IPO_TEXT.replace('This is our initial public offering.','On September 7, 2026, we entered into a securities purchase agreement for a registered direct offering.').replace('China','the United States').replace('initial public offering price','offering price').replace('underwriter','placement agent')
    candidate,_=parse(text,'DIRECT_OFFERING')
    assert candidate.operations_country=='US'
    assert structural(candidate,Config(),EntityList(ENTITIES),NOW).status=='STRUCTURAL_MATCH'
    assert candidate.matches[0].role=='placement_agent'


@pytest.mark.parametrize('extra', ['The combined purchase price includes a share and one warrant.', 'The transaction includes pre-funded warrants.'])
def test_bundled_warrants_require_review(extra):
    candidate,_=parse(IPO_TEXT+extra)
    assert not candidate.terms_unambiguous


def test_conflicting_proceeds_and_unlisted_similar_name_cannot_qualify():
    candidate,_=parse(IPO_TEXT.replace('$20 million','$25 million').replace('Cathay Securities','Cathay SecuritiesX'))
    assert not candidate.terms_unambiguous and not candidate.matches


def test_shelf_and_historical_ipo_mentions_are_not_new_events():
    assert parse('We maintain a shelf registration and an at-the-market program.','DIRECT_OFFERING')[0] is None
    assert parse('We are conducting a secondary offering. Following our initial public offering in 2015, we expanded our operations.')[0] is None
