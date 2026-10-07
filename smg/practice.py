"""Practice message uses actual stored candidates, never synthetic stock alerts."""
import csv
from .models import Candidate
from .firm_first import firm_structure
from .notify import clean


def practice_payload(store,root,now,cfg,entities):
    with (root/'backtest/reference_events.csv').open() as stream:events=list(csv.DictReader(stream))
    reference={r['ticker'] for r in events};rows=[]
    for _,raw in store.items('candidate:'):
        c=Candidate.model_validate(raw)
        if c.ticker not in reference:continue
        check=firm_structure(c,cfg,entities,now)
        rows.append({'ticker':c.ticker,'source_date':str(c.event_date),'firm_check':check.status,'reasons':check.reasons,
                     'firms':[m['name'] for m in check.matches],
                     'source_urls':list(dict.fromkeys(m['evidence']['url'] for m in check.matches))})
    rows.sort(key=lambda r:r['ticker'])
    symbols=sorted({r['ticker'] for r in rows})
    lines=['**DUDEBOT PRACTICE — CURRENT RESEARCH CHECK**',
           f'Compared stored candidates with your {len(events)} reference events / {len(reference)} tickers.',
           'Current overlap: '+(', '.join(symbols) if symbols else 'none in the processed candidates')+'.']
    for row in rows:
        lines.append(f"• {clean(row['ticker'])}: {clean('; '.join(row['firms']))}; {row['firm_check']}; source {row['source_date']}.")
    lines+=['These are current filing matches, not historical detections or qualified stock alerts. Missing issuer classification, stale reviews, market data and halt checks still suppress real alerts.',
            'Historical replay is incomplete. No detection rate is claimed.',
            'Delivery: first newly qualified phase found by the 15-minute weekday scan. Alpaca SIP remains deliberately 16 minutes delayed.']
    text='\n'.join(lines)
    if len(text)>1900:
        text='\n'.join(lines[:3]+['Full per-stock audit is in the workflow artifact.']+lines[-3:])
    samples=[]
    for prefix in ('ranked_evaluation:','evaluation:'):
        for _,row in store.items(prefix):
            if row.get('snapshot'):samples.append(row)
    samples.sort(key=lambda r:r['snapshot']['price_time'],reverse=True)
    return text,{'reference_events':len(events),'reference_symbols':len(reference),'overlap_tickers':symbols,'rows':rows,
                 'card_example':samples[0] if samples else None,
                 'meaning':'Present-day research overlap only; not a historical backtest or a live alert'}


def practice_embed(text,audit,now):
    from .trade_card import embed,position_guide
    from .models import Evaluation
    from pathlib import Path
    import json
    spec=json.loads((Path.cwd()/'config/ranked_firm_alerts.json').read_text(encoding='utf-8'))
    reference=spec.get('drop_probability_reference',{}).get('pooled',{})
    if audit.get('card_example'):
        card=embed(Evaluation.model_validate(audit['card_example']),now,practice=True)
    else:
        first=next(iter(audit['rows']),{})
        card={'title':(first.get('ticker') or 'Dudebot')+' · FIRM WATCH · PRACTICE','color':0xE7AF38,
              'description':'Stored filing association only. Current entry checks are not confirmed.',
              'fields':[{'name':'Why picked · Firm watch','value':clean('; '.join(first.get('firms',[]))) or 'No verified current filing match'},
                        {'name':'Strength score','value':'Unavailable without a complete current scan'},
                        {'name':'Estimated drop probability','value':'No qualified entry; no stock-specific probability assigned'},
                        {'name':'Drop window / hold','value':'Monitor only. If later qualified: 1–3 trading sessions'},
                        {'name':'Suggested paper position','value':'0 shares · $0 allocated; practice/watch only'}],
              'footer':{'text':'PRACTICE ONLY · no trade recommendation'},'timestamp':now.isoformat()}
    guide=position_guide(10,85,True,True)
    targets=reference.get('targets',{})
    probability='Insufficient historical reference data'
    if targets:
        probability=' · '.join(f"{h}d {100*targets[f'day_{h}']['estimate']:.1f}%" for h in (1,2,3))
        probability+=f"\n{reference['samples']} independent past firm entries; not a forecast for the example stock."
    sample={'title':'PRACTICE · Layout and sizing math','color':0x6B7280,
            'description':'Illustration only; no stock is recommended. Score85 and price$10 below are layout examples, not observed live inputs.',
            'fields':[{'name':'Strength score','value':'85/100 · illustrative; not a probability'},
                      {'name':'Historical 20%+ drop reference','value':probability},
                      {'name':'Sizing example','value':f"{guide['shares']:,} shares × $10 = ${guide['capital']:,.2f}\n$100k equity / $150k available BP;20% reserve. A high strength score alone cannot unlock the largest tier."},
                      {'name':'Hold plan','value':'1–3 trading sessions; no guaranteed drop date'}],
            'footer':{'text':'PRACTICE ONLY · current live orders:0'},'timestamp':now.isoformat()}
    return {'username':'Dudebot','content':'**Practice upload · new simplified cards**','embeds':[card,sample],'allowed_mentions':{'parse':[]}}
