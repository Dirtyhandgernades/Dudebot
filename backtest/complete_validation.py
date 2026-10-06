"""Audit missed episodes, validate calibration, and export a frozen candidate."""
import gzip
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from smg.risk_model import samples,feature_row,predict,fit,matured_before
from smg.validation import missed_dumps,independent_rows,fit_calibration,calibrated_scores,reliability


def run():
    source=Path('outputs/backtest/hybrid-37386241124');rank=Path('outputs/backtest/target-rank-2026-10-05')
    out=Path('outputs/backtest/validation-2026-10-05');out.mkdir(parents=True,exist_ok=True)
    packet=json.loads(gzip.decompress((source/'firm-timing-inputs.json.gz').read_bytes()))
    records=json.loads((source/'discovery-decisions.json').read_text())
    rows=samples(records,packet['raw'],packet['split'],packet['sessions'],firm_dates=packet['firm_dates'])
    index={d:i for i,d in enumerate(packet['sessions'])};audit=[]
    for year in (2023,2024,2025):
        bundle=json.loads((rank/f'{year}-model.json').read_text());model=bundle['model']
        events=json.loads((source/f'{year}-hybrid-signals.json').read_text());selected={}
        for day,es in events.items():
            selected[day]=[];i=index[day]
            for e in es:
                history=[packet['split'][e['ticker']][d] for d in packet['sessions'][i-22:i]]
                x=feature_row(history)
                if x and predict(model,[{'x':x}])[0]>=bundle['thresholds']['top_half']:selected[day].append(e)
        result=json.loads((rank/f'{year}-top_half_30pct-50000-base.json').read_text())
        report=missed_dumps(packet,events,selected,result,f'{year}-09-08',f'{year}-12-05')
        (out/f'{year}-missed-dumps.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        audit.append({'year':year,**{k:v for k,v in report.items() if k!='rows'}})
    train=matured_before(rows,'2024-01-01');model=fit(train)
    calibration=independent_rows(matured_before(rows,'2025-01-01','2024-01-01'))
    evaluation=independent_rows(matured_before(rows,'2026-01-01','2025-01-01'))
    raw_cal=predict(model,calibration);platt=fit_calibration(calibration,raw_cal)
    raw_eval=predict(model,evaluation);estimates=calibrated_scores(platt,raw_eval)
    comparison={'status':'RETROSPECTIVE_CALIBRATION_DIAGNOSTIC','model_train_end':'2023-12-31',
        'calibration_end':'2024-12-31','evaluation_year':2025,'evaluation_previously_inspected':True,
        'overlap_policy':'one nonoverlapping label window per ticker',
        'calibrator':platt,'raw_rank_reliability':reliability(evaluation,raw_eval),
        'calibrated_reliability':reliability(evaluation,estimates) if platt else None,
        'confidence_sizing_enabled':False}
    prevalence=sum(r['label'] for r in calibration)/len(calibration) if calibration else 0
    comparison['constant_calibration_prevalence_brier']=sum((prevalence-r['label'])**2 for r in evaluation)/len(evaluation) if evaluation else None
    (out/'calibration.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
    frozen=json.loads((rank/'2025-model.json').read_text())
    # This calibration uses already mature 2025 outcomes. It is frozen before
    # any new prospective 2026 observation; it is not fresh validation itself.
    new_cal=fit_calibration(evaluation,predict(frozen['model'],evaluation))
    spec={'id':'firm-shadow-2026-10-06-v1','frozen_at':datetime.now(timezone.utc).isoformat(),
        'start_date':'2026-10-06','end_date':'2026-12-05','target_drop_fraction':.20,'horizon_sessions':3,
        'model':frozen['model'],'rank_threshold':frozen['thresholds']['top_half'],
        'calibration':new_cal,'confidence_sizing_enabled':False,'live_trade_enabled':False,
        'decision_window_minutes_before_close':30,'data_delay_minutes':16,
        'profiles':{'baseline':{'initial':100000,'position_target':30000,'buying_power':150000,'max_position_equity_fraction':.25},
                    'aggressive':{'initial':100000,'position_target':50000,'buying_power':150000,'max_position_equity_fraction':.30}},
        'input_sha256':hashlib.sha256((source/'firm-timing-inputs.json.gz').read_bytes()).hexdigest(),
        'feature_contract':'Prior 22 complete regular-session minute aggregates; intraday exhaustion research setup',
        'limitations':['Daily-provider training differs from regular-session minute features; prospective calibration required',
            'Prospective observations may be ineligible or unborrowable; detection and execution are separate',
            'No forecast or calibration estimate is an accusation or guaranteed trade outcome']}
    published=Path('config/frozen_forward.json')
    if published.exists():spec=json.loads(published.read_text())
    (out/'frozen-candidate.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
    summary={'audits':audit,'calibration':comparison,'source_coverage':json.loads(Path('outputs/backtest/game-firm-37081288053/discovery-summary.json').read_text()),
        'future_test_status':'PENDING_PROSPECTIVE_OBSERVATIONS'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({'audits':[{'year':a['year'],'events':a['events'],'reasons':a['reason_counts']} for a in audit],
        'raw_brier':comparison['raw_rank_reliability']['brier'],
        'calibrated_brier':(comparison['calibrated_reliability'] or {}).get('brier'),
        'evaluation_samples':len(evaluation),'calibration_samples':len(calibration)}))


if __name__=='__main__':run()
