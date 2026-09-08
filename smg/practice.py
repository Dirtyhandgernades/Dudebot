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
            'Schedule: 12:00 Pacific / 2:00 Central, following daylight saving time. Alpaca SIP remains deliberately 16 minutes delayed.']
    text='\n'.join(lines)
    if len(text)>1900:
        text='\n'.join(lines[:3]+['Full per-stock audit is in the workflow artifact.']+lines[-3:])
    return text,{'reference_events':len(events),'reference_symbols':len(reference),'overlap_tickers':symbols,'rows':rows,
                 'meaning':'Present-day research overlap only; not a historical backtest or a live alert'}


def practice_embed(text,audit,now):
    fields=[{'name':r['ticker']+' · '+r['firm_check'],
             'value':clean('; '.join(r['firms']))[:600]+f"\nSource dated {r['source_date']}",'inline':False} for r in audit['rows'][:20]]
    return {'username':'Dudebot','content':'', 'embeds':[{
        'title':'Dudebot · Practice research check','color':0x39B9A8,
        'description':f"**{audit['reference_events']} reference events · {audit['reference_symbols']} stocks**\nCurrent overlap: **{', '.join(audit['overlap_tickers']) or 'None'}**\n\n"
            'These are current filing matches, not historical detections or qualified stock alerts. Historical replay remains incomplete.',
        'fields':fields[:6]+[{'name':'Delivery & data','value':'12:00 Pacific / 2:00 Central, following daylight saving time. Free Alpaca SIP is delayed 16 minutes.','inline':False},
            {'name':'Hard exclusions','value':'Halted/suspended stocks, SPACs/acquisition corporations, and exactly-five-letter tickers. Unknown checks suppress alerts.','inline':False}],
        'footer':{'text':'Practice only · No trade or detection claim'},'timestamp':now.isoformat()}],
        'allowed_mentions':{'parse':[]}}
