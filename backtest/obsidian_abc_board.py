"""Write-once shadow A/B/C board intake. No discovery, delivery or order claims."""
import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from backtest.obsidian_prospective_journal import timestamp

POLICY = 'OBSIDIAN_ABC_SHADOW_INTAKE_V1_20261029'
CT = ZoneInfo('America/Chicago')


def build(packet, now):
    cutoff = timestamp(packet['cutoff_at'], 'cutoff')
    if now.utcoffset() is None or not cutoff <= now <= cutoff + timedelta(minutes=15):
        raise ValueError('OUTSIDE_PUBLICATION_WINDOW_NO_BACKFILL')
    local = cutoff.astimezone(CT)
    if (local.hour, local.minute, local.second, local.microsecond) != (14,20,0,0):
        raise ValueError('WRONG_CHECKPOINT')
    if packet.get('exchange_session_verified') is not True or not packet.get('calendar_receipt'):
        raise ValueError('EXCHANGE_SESSION_UNVERIFIED')
    roster = packet['universe']
    if not isinstance(roster,list) or not roster or any(not isinstance(x,str) or not x for x in roster) or len(set(roster)) != len(roster):
        raise ValueError('INVALID_UNIVERSE')
    if not packet.get('universe_receipt'):
        raise ValueError('UNIVERSE_PROVENANCE_REQUIRED')
    rows = packet['rows']
    if not isinstance(rows,list) or any(not isinstance(x,dict) for x in rows):
        raise ValueError('INVALID_ROWS')
    symbols=[r.get('ticker') for r in rows]
    if len(symbols)!=len(set(symbols)) or set(symbols)!=set(roster):
        raise ValueError('INCOMPLETE_OR_DUPLICATE_CANDIDATE_REJECTION_COVERAGE')
    output=[]
    for row in rows:
        reasons=[]
        category=row.get('classification')
        if category not in {'A','B','C','BLOCKED'}:
            raise ValueError('INVALID_CLASSIFICATION')
        observed=timestamp(row['observed_at'],'observed')
        if observed>cutoff:
            raise ValueError('FUTURE_OBSERVATION')
        if cutoff-observed>timedelta(minutes=5): reasons.append('STALE_OBSERVATION')
        if row.get('source_latency_verified') is not True: reasons.append('SOURCE_LATENCY_UNKNOWN')
        if not row.get('source_receipts'): reasons.append('SOURCE_RECEIPTS_MISSING')
        if category in {'A','C'}:
            for key in ('catalyst_public_at','catalyst_observed_at','market_at'):
                if not row.get(key): reasons.append('MISSING_'+key.upper());continue
                clock=timestamp(row[key],key)
                if clock>cutoff or clock>observed: raise ValueError('FUTURE_'+key.upper())
                if key=='market_at' and cutoff-clock>timedelta(minutes=5): reasons.append('STALE_MARKET_DATA')
            if row.get('mechanism_verified') is not True: reasons.append('MECHANISM_UNVERIFIED')
            if row.get('counterevidence_reviewed') is not True: reasons.append('COUNTEREVIDENCE_UNREVIEWED')
            if row.get('halt_clear') is not True: reasons.append('HALT_UNKNOWN_OR_ACTIVE')
            if category=='A' and row.get('principal_collapse_not_occurred') is not True:
                reasons.append('EARLY_STATUS_UNVERIFIED')
            if category=='C' and row.get('thesis_invalidation_verified') is not True:
                reasons.append('REVERSAL_UNVERIFIED')
        output.append(dict(original=row, classification='BLOCKED' if reasons else category,
                           blockers=reasons, executable=False, trade_authorized=False))
    return dict(mode='RESEARCH_ONLY_NOT_AN_ORDER',policy_version=POLICY,cutoff_at=cutoff.isoformat(),
                created_at=now.isoformat(),universe=roster,universe_receipt=packet['universe_receipt'],
                calendar_receipt=packet['calendar_receipt'],rows=output,denominator=len(roster),
                counts=dict(Counter(r['classification'] for r in output)),
                horizons=[0,1,2,3],outcomes=None,delivery_verified=False,smg_eligibility_verified=False,
                coverage_scope='SUPPLIED_SUPPORTED_UNIVERSE_NOT_CERTIFIED_FULL_MARKET')


def write(packet_path, output_path, now=None):
    # A caller cannot backdate the CLI publication clock or overwrite a prior board.
    raw=Path(packet_path).read_bytes()
    result=build(json.loads(raw),now or datetime.now(timezone.utc))
    result['input_sha256']=hashlib.sha256(raw).hexdigest()
    with Path(output_path).open('x') as handle: json.dump(result,handle,indent=2,sort_keys=True)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    args=p.parse_args();write(args.packet,args.out)


if __name__=='__main__':main()
