"""Dated same-security identity maintenance, never winner selection."""
from copy import deepcopy
from datetime import date
from .decision_evidence import stamp
from .market import session_bounds
from .swing_backtest import stitch_rename


def usable_rename(change,end):
    published=stamp(change.get('published_at'));effective=change.get('effective_date','9999-99-99')
    try:bounds=session_bounds(date.fromisoformat(effective))
    except ValueError:return False
    return bool(change.get('action')=='rename_only' and effective<=end and published and bounds and published<=bounds[0] and change.get('source_url'))


def apply_renames(data,records,first,changes,end):
    audit=[]
    for change in changes:
        if not usable_rename(change,end):continue
        old=change['old_symbol'];new=change['new_symbol'];effective=change['effective_date']
        if old not in first:continue
        before={mode:{d:deepcopy(b) for d,b in data[mode].get(old,{}).items() if d<effective} for mode in ('raw','split')}
        result=stitch_rename(data,change);audit.append(result)
        if result['status']!='STITCHED_RENAME':continue
        # Use the aligned old-unit series for both identities. Old identity is
        # for earlier decisions and position valuation; new decisions start at
        # the effective session and retain the original issuer's history.
        for mode in ('raw','split'):
            data[mode][new]={**before[mode],**{d:deepcopy(b) for d,b in data[mode][old].items() if d>=effective}}
        first[new]=max(effective,min(first[old],first.get(new,effective)))
        for row in list(records):
            if row.get('ticker')!=old:continue
            available=stamp(row.get('decision_at'))
            if available is None:continue
            cloned=deepcopy(row);cloned['ticker']=new
            cloned['decision_at']=max(available,stamp(change['published_at']),session_bounds(date.fromisoformat(effective))[0]).isoformat()
            cloned['identity_source']=change['source_url'];records.append(cloned)
    return audit
