"""Fixed historical seven-feature rank applied as an uncalibrated shadow only."""
from datetime import date,timedelta
import hashlib,json,math
from pathlib import Path
from smg.market import calendar,session_bounds
from smg.risk_model import feature_row,predict,FEATURES
from backtest.obsidian_prospective_capture import EASTERN,asof


def prior_sessions(now):
    cal=calendar(now.year);day=now.astimezone(EASTERN).date().isoformat()
    days=[str(d.date()) for d in cal.sessions_in_range(str(now.date()-timedelta(days=60)),day) if str(d.date())<day]
    return days[-22:]


def rank_symbols(symbols,split,raw,now,document):
    model=document['model']
    if tuple(model['features'])!=FEATURES or len(model['weights'])!=7:raise ValueError('MODEL_FEATURE_CONTRACT_CHANGED')
    if document['training_last_label_date']>=now.astimezone(EASTERN).date().isoformat():raise ValueError('MODEL_NOT_TRAINED_BEFORE_DECISION')
    expected=prior_sessions(now);result={}
    if len(expected)!=22:raise ValueError('EXPECTED_22_PRIOR_EXCHANGE_SESSIONS')
    for symbol in symbols:
        index={};bad=False
        for bar in split.get(symbol,[]):
            at=asof(bar.get('t')) if isinstance(bar,dict) else None
            if at is None or at>now:bad=True;break
            day=at.astimezone(EASTERN).date().isoformat()
            if day not in expected:continue
            if (any(type(bar.get(k)) not in (int,float) or not math.isfinite(bar[k]) or bar[k]<=0 for k in ('o','h','l','c')) or
                bar['h']<max(bar['o'],bar['c']) or bar['l']>min(bar['o'],bar['c']) or
                type(bar.get('v')) not in (int,float) or not math.isfinite(bar['v']) or bar['v']<0):bad=True;break
            if day in index:bad=True;break
            index[day]=bar
        history=[index.get(day) for day in expected]
        raw_prior=[b for b in raw.get(symbol,[]) if asof(b.get('t')) is not None and asof(b['t']).astimezone(EASTERN).date().isoformat()==expected[-1]]
        if bad or not all(history) or len(raw_prior)!=1 or type(raw_prior[0].get('c')) not in (int,float) or not math.isfinite(raw_prior[0]['c']) or raw_prior[0]['c']<=0:
            result[symbol]={'status':'INCOMPLETE_DUPLICATE_OR_FUTURE_DAILY_FEATURES','score':None};continue
        try:features=feature_row(history)
        except (ValueError,KeyError,TypeError,ZeroDivisionError):features=None
        if features is None or not all(math.isfinite(f) for f in features):
            result[symbol]={'status':'INVALID_DAILY_FEATURES','score':None};continue
        value=predict(model,[{'x':features}])[0]
        result[symbol]=dict(status='CONDITIONAL_ORDINAL_SHADOW_RANK',score=value,score_is_calibrated_probability=False,
                            feature_start=expected[0],last_complete_feature_session=expected[-1],
                            prior_raw_close=raw_prior[0].get('c'),features=dict(zip(FEATURES,features)),
                            historical_training_top_half_threshold=document['thresholds']['top_half'],
                            model_validated_for_live_use=False,population_match_verified=False,
                            population_warning='Free watchlist has no verified historical hybrid-trigger/firm-asof match; score is diagnostic only',trade_authorized=False)
    return result


def fetch_ranks(reader,symbols,now,headers,model_path):
    path=Path(model_path);document=json.loads(path.read_text());days=prior_sessions(now);payloads={};receipts=[]
    for adjustment in ('raw','split'):
        params=dict(symbols=','.join(symbols),timeframe='1Day',feed='sip',adjustment=adjustment,
                    start=days[0]+'T00:00:00Z',end=session_bounds(date.fromisoformat(days[-1]))[1].isoformat(),limit=10000)
        body,receipt=reader.get('https://data.alpaca.markets/v2/stocks/bars',params=params,headers=headers);receipts.append(receipt)
        try:value=json.loads(body) if body is not None else None
        except ValueError:value=None
        if (not isinstance(value,dict) or not isinstance(value.get('bars'),dict) or value.get('next_page_token') or
            any(not isinstance(b,list) for b in value['bars'].values()) or set(value['bars'])-set(symbols)):
            return {s:dict(status=receipt['error'] or 'INCOMPLETE_DAILY_RANK_RESPONSE',score=None) for s in symbols},dict(model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),requests=receipts)
        payloads[adjustment]=value['bars']
    return rank_symbols(symbols,payloads['split'],payloads['raw'],now,document),dict(model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),training_last_label_date=document['training_last_label_date'],requests=receipts,model_promoted=False)
