"""Bounded source audit of independent historical filing leads.

This stage does not certify a candidate universe or issue historical alerts.
It saves real source evidence and parser failures for subsequent mapping and
point-in-time context review. Both pipeline queues persist separately.
"""
import hashlib
import json
import os
import re
import sqlite3
import time
from datetime import timedelta

from bs4 import BeautifulSoup

from .extraction import LocalParser
from .rules import years_ago
from .transport import Http


def audit_filings(state, start, end, entries, budget=40):
    from .backtest import public_at, write_json
    index = state / 'indexes.sqlite'
    if not index.exists() or '@' not in os.environ.get('SEC_USER_AGENT', ''):
        return {'status':'NOT_RUN', 'reason':'INDEX_OR_SEC_ACCESS_MISSING'}, []
    db = sqlite3.connect(index)
    db.row_factory = sqlite3.Row
    db.execute('CREATE TABLE IF NOT EXISTS parsed_filings (pipeline TEXT, path TEXT, result TEXT, PRIMARY KEY(pipeline,path))')
    queues = {
        'RECENT_IPO':("form='424B4'", str(years_ago(start, 3))),
        'DIRECT_OFFERING':("form IN ('424B3','424B5','8-K','6-K')", str(start-timedelta(days=30)))
    }
    http = Http(); parser = LocalParser(entries); errors = []; downloaded = 0; started = time.monotonic()
    try:
        for pipeline, (form_filter, since) in queues.items():
            # Separate quotas prevent the much larger direct queue starving IPOs.
            jobs = db.execute(f'''SELECT * FROM leads WHERE {form_filter} AND filed_at>=? AND filed_at<=?
                AND path NOT IN (SELECT path FROM parsed_filings WHERE pipeline=?)
                ORDER BY filed_at, path LIMIT ?''', (since, str(end), pipeline, max(0,budget//2))).fetchall()
            for job in jobs:
                if time.monotonic()-started > 360:
                    errors.append('FILING_AUDIT_TIME_BUDGET'); break
                url = 'https://www.sec.gov/Archives/' + job['path']
                source_path = state / 'filings' / (hashlib.sha256(url.encode()).hexdigest()+'.json')
                try:
                    if source_path.exists():
                        doc = json.loads(source_path.read_text())
                    else:
                        raw = http.text(url, headers={'User-Agent':os.environ['SEC_USER_AGENT']})
                        # Reject SEC block pages served with a misleading success status.
                        if not re.search(r'<SEC-DOCUMENT>|<html|<!DOCTYPE', raw, re.I):
                            raise ValueError('UNRECOGNIZED_FILING_CONTENT')
                        soup = BeautifulSoup(raw, 'html.parser')
                        for element in soup(['script','style','ix:header']): element.decompose()
                        text = ' '.join(soup.get_text(' ', strip=True).split())
                        doc = dict(url=url,raw_text=raw,text=text,sha256=hashlib.sha256(raw.encode()).hexdigest(),date=job['filed_at'])
                        write_json(source_path,doc); downloaded += 1
                    # Source-derived ticker suggestions only, never today's universe.
                    patterns = [r'(?:under|trading under)\s+the\s+(?:trading\s+)?(?:symbol|ticker)\s+["\u201c\u201d\u2018\u2019\']([A-Z]{1,6})["\u201c\u201d\u2018\u2019\']']
                    symbols = sorted({m for pattern in patterns for m in re.findall(pattern,doc['text'])})
                    ticker = symbols[0] if len(symbols)==1 else 'UNKNOWN'
                    now = public_at({'filed_at':job['filed_at']})
                    context = dict(pipeline=pipeline, date=job['filed_at'], ticker=ticker, cik=job['cik'],
                                   name=job['name'],accession=job['path'].rsplit('/',1)[-1])
                    candidate = parser.extract(context,[doc],now)
                    # The production parser assumes a Nasdaq-filtered input universe.
                    # This independent lead audit has no such guarantee.
                    if candidate:
                        candidate.exchange='UNVERIFIED'
                    result = dict(pipeline=pipeline, url=url, cik=job['cik'], name=job['name'], filed_at=job['filed_at'],
                        ticker_suggestions=symbols, status='TRANSACTION_LEAD' if candidate else 'NO_TRANSACTION_RECOGNIZED_BY_PARSER',
                        candidate=candidate.model_dump(mode='json') if candidate else None,
                        gaps=['HISTORICAL_MAPPING_UNVERIFIED','CONTEXT_AND_CANCELLATION_REVIEW_PENDING','HALT_ARCHIVE_MISSING'],
                        source_sha256=doc['sha256'])
                    with db:
                        db.execute('INSERT INTO parsed_filings VALUES (?,?,?)',(pipeline,job['path'],json.dumps(result)))
                except Exception as exc:
                    errors.append({'source_url':url,'error_type':type(exc).__name__,'http_status':getattr(exc,'status',None)})
                    # Provider access failure should not hammer the remaining queue.
                    if getattr(exc,'status',None) in {401,403,429}:
                        break
        records = [json.loads(r[0]) for r in db.execute('SELECT result FROM parsed_filings ORDER BY pipeline,path')]
        counts = {}
        for pipeline, (form_filter, since) in queues.items():
            total = db.execute(f'SELECT count(*) FROM leads WHERE {form_filter} AND filed_at>=? AND filed_at<=?',(since,str(end))).fetchone()[0]
            subset = [r for r in records if r['pipeline']==pipeline]
            counts[pipeline] = dict(indexed_leads=total, audited_filings=len(subset),
                transaction_leads=sum(r['candidate'] is not None for r in subset),
                pending_filings=total-len(subset))
        return {'status':'PARTIAL_SOURCE_AUDIT','downloaded_this_run':downloaded,'pipelines':counts,'errors':errors,
                'universe_complete':False,'screening_detections':None}, records
    finally:
        db.close()
