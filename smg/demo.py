"""Deterministic synthetic records. This module cannot send Discord messages."""
from datetime import date,datetime,timedelta,timezone
from .models import Candidate,Evidence,EntityMatch,Snapshot,HaltCheck
from .rules import evaluate
UTC=timezone.utc
NOW=datetime(2026,9,8,20,0,5,tzinfo=UTC)

def candidate(ticker='DEMO',pipeline='RECENT_IPO'):
    evidence=Evidence(url='https://example.com/SYNTHETIC-FILING',filed_at=date(2026,7,15),quote='SYNTHETIC FIXTURE ONLY: an operating company offers 4 million common shares at $5, raising $20 million.',document_sha256='synthetic-fixture')
    return Candidate(pipeline=pipeline,cik='9999999999',ticker=ticker,name='Synthetic Example Company (not a real issuer)',event_id='IPO' if pipeline=='RECENT_IPO' else '2026-09-07',exchange='XNAS',operations_country='CN',ipo_date=date(2026,7,15),event_date=date(2026,7,15) if pipeline=='RECENT_IPO' else date(2026,9,7),status='closed',security_type='CS',is_acquisition_corp=False,offer_price=5,offer_gross=20_000_000,currency='USD',base_shares=4_000_000,terms_unambiguous=True,
        matches=[EntityMatch(name='Cathay Securities',role='underwriter',relationship='transaction',evidence=evidence)],
        evidence={key:evidence for key in ['operations_country','ipo_date','offer_price','offer_gross','is_acquisition_corp','security_type','status']},notes=['Synthetic test fixture; no live securities were screened.'],reviewed_at=NOW)

def snapshot(now=NOW):
    return Snapshot(asof=now,price_time=now.replace(second=0)-timedelta(minutes=1),price=18,monthly_return=180,one_day_return=12,five_day_return=42,drawdown_pct=-5,rvol=2.2,rvol20=1.8,baseline_sessions=38,cumulative_volume=2_200_000,baseline_volume=1_000_000,source_url='https://example.com/SYNTHETIC-MARKET-DATA',flags=['SHORT_BASELINE'],market_cap=100_000_000,market_cap_observed_at=now-timedelta(minutes=1),market_cap_source='https://example.com/SYNTHETIC-CAP',market_cap_basis='synthetic')

def run_demo(cfg,entities):
    demo_cfg=cfg.model_copy(update={'surge_return_min_pct':100})
    clear=HaltCheck(checked_at=NOW,status='CLEAR',reason='Synthetic status',source_url='https://example.com/SYNTHETIC-HALTS')
    variants=[candidate(),candidate('HALT'),candidate('FIVER'),candidate('SPAC'),candidate('RVOL'),candidate('DOFR','DIRECT_OFFERING')]
    variants[3].is_acquisition_corp=True;variants[5].operations_country='US'
    results=[]
    for c in variants:
        market=snapshot();halt=clear
        if c.ticker=='HALT':halt=clear.model_copy(update={'status':'HALTED'})
        if c.ticker=='RVOL':market.rvol=.8
        results.append(evaluate(c,demo_cfg,entities,NOW,market,halt))
    return results,NOW
