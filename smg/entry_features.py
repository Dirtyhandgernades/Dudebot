"""Time-stamped entry diagnostics; historical associations are not fraud proof."""
import math
from datetime import datetime,timedelta
from smg.risk_model import feature_row
from smg.rules import normalize_name

FEATURES=('return21','return5','return1','drawdown21','volume_ratio','failed_low','range',
          'prior_upper_wick','prior_close_location','return3','recent_volume_trend',
          'focus_auditor','focus_underwriter','focus_counsel','financing_news','healthcare_news','news_available')


def before_news(rows,at):
    kept=[]
    for row in rows:
        try:
            created=datetime.fromisoformat(row['created_at'].replace('Z','+00:00'))
            updated=datetime.fromisoformat((row.get('updated_at') or row['created_at']).replace('Z','+00:00'))
            if created.tzinfo and updated.tzinfo and at-timedelta(days=7)<=created<=at and updated<=at:kept.append(row)
        except (KeyError,TypeError,ValueError):continue
    return kept


def context(records,at,entities):
    priorities={};links=[]
    for row in records:
        try:stamp=datetime.fromisoformat(row['decision_at'].replace('Z','+00:00'))
        except (KeyError,TypeError,ValueError):continue
        if stamp.tzinfo is None or stamp>at:continue
        for m in row.get('firm_matches',[]):
            role='underwriter' if m['role']=='placement_agent' else m['role']
            party=entities.get((role,normalize_name(m['name'])))
            if not party:continue
            priorities[role]=min(priorities.get(role,99),party['priority'])
            links.append({'name':m['name'],'role':role,'priority':party['priority'],
                          'public_at':stamp.isoformat(),'url':m.get('evidence',{}).get('url') or row.get('source_url'),
                          'relationship':m.get('relationship','source-dated; engagement unconfirmed')})
    return priorities,links


def features(history,records,news,at,entities):
    base=feature_row(history)
    if base is None:return None
    last=history[-1];span=last['h']-last['l'];old=sum(r['v'] for r in history[-11:-6]);recent=sum(r['v'] for r in history[-6:-1])
    priorities,_=context(records,at,entities);headlines=before_news(news,at)
    from smg.mechanism_audit import news_topics
    topics=news_topics(headlines)
    values=base+[(last['h']-max(last.get('o',last['c']),last['c']))/span if span>0 else 0,
        (last['c']-last['l'])/span if span>0 else .5,last['c']/history[-4]['c']-1,
        math.log1p(recent/old) if old>0 else 0,
        float(priorities.get('auditor',99)<=0),float(priorities.get('underwriter',99)<=1),
        float(priorities.get('counsel',99)<=1),float('FINANCING_MENTION' in topics),
        float('HEALTHCARE_CATALYST' in topics),float(bool(headlines))]
    return values if all(math.isfinite(v) for v in values) else None


def chart(history,partial):
    """Current candle uses only the observed partial bar, never the final close."""
    if not history or not partial or any(k not in partial for k in ('o','h','l','c')):return None
    prior=history[-1];span=partial['h']-partial['l']
    if span<=0 or prior['c']<=0:return None
    return {'change_from_prior_close':partial['c']/prior['c']-1,
        'close_location':(partial['c']-partial['l'])/span,
        'upper_wick':(partial['h']-max(partial['o'],partial['c']))/span,
        'red_candle':partial['c']<partial['o'],'below_prior_low':partial['c']<prior['l'],
        'lower_high':partial['h']<prior['h'],
        'failed_recent_high':partial['h']>=max(r['h'] for r in history[-5:]) and partial['c']<max(r['h'] for r in history[-5:])}


def confirmed(value):
    if not value:return False
    return value['below_prior_low'] or (value['red_candle'] and value['close_location']<=.35 and value['change_from_prior_close']<=.02)
