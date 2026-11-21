"""Derived valuation-only same-security rename bridge. Original data unchanged."""
import argparse,copy,gzip,hashlib,json,math
from pathlib import Path
from bs4 import BeautifulSoup
from smg.swing_backtest import stitch_rename


def daily_rows(payload,symbol):
    rows=payload.get('bars',{}).get(symbol,[])
    if not isinstance(rows,list) or not rows:raise ValueError('MISSING_SOURCE_BARS_'+symbol)
    result={}
    for bar in rows:
        day=bar.get('t','')[:10]
        if (not '2025-08-01'<=day<='2025-12-31' or day in result or
            any(type(bar.get(k)) not in (int,float) or not math.isfinite(bar[k]) or bar[k]<=0 for k in ('o','h','l','c'))):
            raise ValueError('INVALID_OR_DUPLICATE_VENDOR_BAR')
        result[day]=bar
    return result


def overlap_check(old,new,before):
    overlap=sorted(d for d in set(old)&set(new) if d<before)
    if len(overlap)<5:raise ValueError('INSUFFICIENT_RENAME_OVERLAP')
    if any(any(abs(old[d][k]-new[d][k])>1e-7 for k in ('o','h','l','c')) for d in overlap):
        raise ValueError('RAW_RENAME_OVERLAP_DISAGREES')
    return overlap


def repair(source,probe,registration,out):
    source,probe,out=Path(source),Path(probe),Path(out)
    if out.exists():raise FileExistsError(out)
    raw=source.read_bytes();spec=json.loads(Path(registration).read_text())
    if hashlib.sha256(raw).hexdigest()!=spec['input_packet_sha256']:raise ValueError('ORIGINAL_PACKET_CHANGED')
    packet=json.loads(gzip.decompress(raw));derived=copy.deepcopy(packet)
    diagnostics=json.loads((probe/'summary.json').read_text());data={}
    for p in diagnostics['market_probes']:
        if p.get('status')!='DAILY_BARS_RETRIEVED_UNVERIFIED_IDENTITY':raise ValueError('SOURCE_PROBE_INCOMPLETE')
        path=probe/'raw-responses'/p['receipt']['archived_response_file'];body=path.read_bytes()
        if hashlib.sha256(body).hexdigest()!=p['receipt']['archived_sha256']:raise ValueError('PROBE_RECEIPT_HASH_CHANGED')
        data[p['adjustment']]=json.loads(body)
    if set(data)!={'raw','split'}:raise ValueError('BOTH_RAW_AND_SPLIT_REQUIRED')
    documents={d['saved_file']:(d['saved_sha256'],d['url']) for case in diagnostics.get('cases',[]) for d in case.get('documents',[]) if d.get('saved_file')}
    announcement=diagnostics.get('brea_issuer_announcement_receipt') or {}
    if announcement.get('archived_sha256'):
        documents['BREA-issuer-announcement.html']=(announcement['archived_sha256'],announcement['source_url'])
    out.mkdir(parents=True);reports=[]
    for change in spec['cases']:
        doc=probe/change['document_name']
        if not doc.is_file():raise ValueError('PRIMARY_RENAME_DOCUMENT_MISSING')
        if documents.get(change['document_name'])!=(hashlib.sha256(doc.read_bytes()).hexdigest(),change['source_url']):raise ValueError('PRIMARY_RENAME_RECEIPT_NOT_BOUND')
        text=BeautifulSoup(doc.read_text(),'html.parser').get_text(' ',strip=True)
        if any(term.casefold() not in text.casefold() for term in change['required_phrases']):raise ValueError('PRIMARY_RENAME_LANGUAGE_NOT_VERIFIED')
        old,new=change['old_symbol'],change['new_symbol']
        if new in packet['raw'] or new in packet['split']:raise ValueError('ALIAS_ALREADY_IN_ORIGINAL_UNIVERSE_REQUIRES_EXPLICIT_MERGE_REVIEW')
        nr=daily_rows(data['raw'],new);ns=daily_rows(data['split'],new)
        overlap=overlap_check(packet['raw'][old],nr,change['effective_date'])
        known_sessions=set(packet['sessions'])
        derived['raw'][new]={d:b for d,b in nr.items() if d in known_sessions}
        derived['split'][new]={d:b for d,b in ns.items() if d in known_sessions}
        report=stitch_rename(derived,change)
        if report['status']!='STITCHED_RENAME':raise ValueError('NO_POST_RENAME_BARS')
        if new not in packet['raw']:derived['raw'].pop(new)
        if new not in packet['split']:derived['split'].pop(new)
        report.update(overlap_sessions_exact=len(overlap),primary_source_sha256=hashlib.sha256(doc.read_bytes()).hexdigest(),
                      first_original_missing_session_recovered=min(d for d in derived['raw'][old] if d not in packet['raw'][old]),
                      original_raw_sessions=len(packet['raw'][old]),derived_raw_sessions=len(derived['raw'][old]),
                      original_dataset_last_session=max(packet['sessions']),full_corporate_action_history_verified=False)
        reports.append(report)
    if set(derived['raw'])!=set(packet['raw']) or derived['sessions']!=packet['sessions']:raise ValueError('ORIGINAL_UNIVERSE_OR_SESSION_SET_CHANGED')
    derived['derived_dataset_restriction']='VALUATION_CONTINUITY_ONLY; original archived signals are not reconstructed; no new entry model replay approved'
    saved=gzip.compress(json.dumps(derived,sort_keys=True).encode(),mtime=0)
    (out/'valuation-continuity-inputs.json.gz').write_bytes(saved)
    summary=dict(status='DERIVED_VENDOR_VALUATION_CONTINUITY_REPAIRED_NOT_STRATEGY_VALIDATED',original_input_sha256=hashlib.sha256(raw).hexdigest(),derived_input_sha256=hashlib.sha256(saved).hexdigest(),
                 original_modified=False,universe_unchanged=True,sessions_unchanged=True,repairs=reports,
                 official_closes_verified=False,SMG_execution_verified=False,performance_recomputed=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True));return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',default='outputs/backtest/hybrid-37386241124/firm-timing-inputs.json.gz')
    p.add_argument('--probe',required=True);p.add_argument('--registration',default='backtest/evidence/2026-11-20/strategy-overhaul/continuity-repair-registration.json');p.add_argument('--out',required=True)
    a=p.parse_args();print(json.dumps(repair(a.source,a.probe,a.registration,a.out),sort_keys=True))
if __name__=='__main__':main()
