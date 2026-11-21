"""Bounded resumable OBSIDIAN lab; no schedules, production or trading calls."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

from backtest import target_rank_research
from backtest.obsidian_strategy_lab import run as audit,hashfile
from backtest.obsidian_rank_control import run as control
from backtest.obsidian_portfolio_guard import propose

SOURCE=Path('outputs/backtest/hybrid-37386241124')
BASELINE=Path('outputs/backtest/target-rank-2026-10-05')
REGISTRY=Path('backtest/evidence/2026-11-20/strategy-overhaul')


def write(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2,sort_keys=True));temp.replace(path)


def checkpoint_identity():
    files=[SOURCE/'firm-timing-inputs.json.gz',SOURCE/'discovery-decisions.json',
           *[SOURCE/f'{year}-hybrid-signals.json' for year in (2023,2024,2025)],
           *[SOURCE/f'{year}-intraday-audit.json' for year in (2023,2024,2025)],
           REGISTRY/'experiment-registration.json',REGISTRY/'ranking-control-registration.json',
           Path('backtest/target_rank_research.py'),Path('backtest/obsidian_strategy_lab.py'),
           Path('backtest/obsidian_rank_control.py'),Path('smg/swing_backtest.py'),Path('smg/risk_model.py'),
           Path('backtest/obsidian_research_runner.py'),Path('backtest/obsidian_portfolio_guard.py'),
           Path('backtest/obsidian_data_audit.py'),Path('backtest/confirmation_comparison.py'),
           Path('smg/intraday_replay.py'),Path('smg/exposure.py'),Path('smg/market.py'),
           Path('smg/models.py'),Path('requirements-tested.txt')]
    return {str(p):hashfile(p) for p in files}


def verify_phase(root,manifest):
    for name,expected in manifest['files'].items():
        if not (root/name).is_file() or hashfile(root/name)!=expected:raise ValueError('CHECKPOINT_OUTPUT_CHANGED: '+name)


def run(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);identity=checkpoint_identity()
    file=out/'checkpoint.json'
    state=json.loads(file.read_text()) if file.exists() else dict(version=1,input_code_hashes=identity,completed={})
    if state['input_code_hashes']!=identity:raise ValueError('CHECKPOINT_INPUT_CHANGED_CREATE_NEW_VERSION')
    def phase(name,call):
        if name in state['completed']:
            verify_phase(Path('.'),state['completed'][name]);return
        paths=call()
        state['completed'][name]=dict(files={str(p):hashfile(p) for p in paths},completed_at_utc=datetime.now(timezone.utc).isoformat())
        write(file,state)
    def baseline():
        summary=BASELINE/'summary.json'
        if not summary.exists():target_rank_research.run()
        r=json.loads(summary.read_text())
        if r['input_sha256']!=identity[str(SOURCE/'firm-timing-inputs.json.gz')]:raise ValueError('BASELINE_INPUT_MISMATCH')
        files=sorted(BASELINE.glob('*.json'))+sorted(BASELINE.glob('*.csv'))
        if len(r['results'])!=54:raise ValueError('INCOMPLETE_ORIGINAL_54_PORTFOLIOS')
        return files
    phase('unchanged_baseline',baseline)
    def forensic():
        audit(SOURCE,BASELINE,REGISTRY/'experiment-registration.json',out/'forensics')
        return sorted((out/'forensics').glob('*'))
    phase('forensics_and_registered_risk_experiments',forensic)
    def benchmark():
        control(SOURCE,BASELINE,REGISTRY/'ranking-control-registration.json',out/'rank-control')
        return sorted((out/'rank-control').glob('*'))
    phase('unranked_and_cash_controls',benchmark)
    r=json.loads((out/'forensics/summary.json').read_text())
    now=datetime.now(timezone.utc)
    paper=propose({},dict(ticker='NO_QUALIFIED_LIVE_COMPONENT',thesis='Historical results do not supply current account facts'),now)
    summary=dict(status='ACTUAL_BOUNDED_RESEARCH_COMPLETED_NOT_PROMOTABLE',baseline_reproduced=r['reproduction'],
                 original_variant_count=r['original_variant_count'],audit_trade_rows=r['trade_audit_rows'],
                 independent_trade_count_not_audit_row_count=True,
                 completed_steps=list(state['completed']),paper_account_gate=paper,
                 strategy_promotion=False,production_changed=False,actual_order_submitted=False,
                 blockers=['No untouched independent evaluation periods','No authenticated historical SMG/cap/borrow/halts',
                           'Archive ends Dec5 rather than full Aug-Dec','No current SMG-scoped read tool in this execution environment',
                           'Source-window gaps remain, global market/catalyst recall unmeasured',
                           'Original prospective official-close proof contract still unfulfilled'])
    write(out/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);a=p.parse_args()
    r=run(a.out);print(json.dumps(r,sort_keys=True))
if __name__=='__main__':main()
