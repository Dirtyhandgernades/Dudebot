from datetime import datetime,timezone
from collections import defaultdict
from smg.decision_evidence import execution_evidence,latest_known
from smg.mechanism_audit import roles_before
from smg.market import calendar
from backtest.repair_study import build_rows,held_issuer,portfolio


def test_later_role_publication_cannot_change_same_close_features():
    records=defaultdict(list,TEST=[{'ticker':'TEST','decision_at':'2025-09-08T21:00:00Z','source_url':'https://example.com/late',
        'firm_matches':[{'name':'A','role':'auditor','relationship':'current'}]}])
    assert roles_before(records,'TEST','2025-09-08')==[]
    assert roles_before(records,'TEST','2025-09-09')[0]['name']=='A'


def test_execution_unknown_is_not_executable_and_failure_does_not_resurrect_old_pass():
    result=execution_evidence('TEST','2025-09-08T19:00:00Z',10)
    assert result['status']=='UNAVAILABLE' and len(result['missing'])==5
    rows=[{'kind':'borrow','subject':'TEST','observed_at':'2025-09-08T18:30:00Z','source':'https://example.com',
           'value':{'status':'VERIFIED','tradable':True,'shortable':True,'borrow_status':'easy_to_borrow'}},
          {'kind':'borrow','subject':'TEST','observed_at':'2025-09-08T18:45:00Z','source':'https://example.com',
           'value':{'status':'UNAVAILABLE'}}]
    chosen=latest_known(rows,'borrow','TEST',datetime(2025,9,8,19,tzinfo=timezone.utc),3600)
    assert chosen['value']['status']=='UNAVAILABLE'
    assert execution_evidence('TEST','2025-09-08T19:00:00Z',10,rows)['status']=='UNAVAILABLE'


def test_execution_future_provenance_and_hard_exclusions_cannot_pass():
    facts={'security':{'exchange':'XNAS','is_acquisition_corp':False,'security_type':'CS'},
           'market_cap':{'market_cap':30_000_000},'halt':{'halt_status':'CLEAR'},
           'borrow':{'tradable':True,'shortable':True,'borrow_status':'easy_to_borrow'},'smg_membership':{'allowed':True}}
    rows=[{'kind':k,'subject':'TEST','observed_at':'2025-09-08T18:30:00Z','source':'https://example.com',
           'value':{'status':'VERIFIED',**v}} for k,v in facts.items()]
    assert execution_evidence('TEST','2025-09-08T19:00:00Z',10,rows)['status']=='EXECUTABLE_INDICATION'
    rows[0]['published_at']='2025-09-08T20:00:00Z'
    assert execution_evidence('TEST','2025-09-08T19:00:00Z',10,rows)['status']=='UNAVAILABLE'
    assert execution_evidence('ABVC','2025-09-08T19:00:00Z',10)['status']=='REJECTED'
    assert execution_evidence('ABCDE','2025-09-08T19:00:00Z',10)['status']=='REJECTED'
    assert execution_evidence('TEST','2025-09-08T19:00:00Z',3,rows)['status']=='REJECTED'


def packet():
    days=[str(s.date()) for s in calendar(2025).sessions_in_range('2025-07-01','2025-10-01')]
    series={d:{'o':10,'c':10,'h':10.1,'l':9.9,'v':100} for d in days}
    # Watch before a next-close gap down; it must not profit from that gap.
    series[days[30]]={'o':15,'c':15,'h':15.1,'l':14.9,'v':100}
    for d in days[31:]:series[d]={'o':5,'c':5,'h':5.1,'l':4.9,'v':100}
    return {'sessions':days,'first_dates':{'TEST':days[0]},'raw':{'TEST':series},'split':{'TEST':series},'news':{}},days


def test_next_close_entry_cannot_claim_the_intervening_gap_as_profit():
    data,days=packet();rows,gaps,first=build_rows(data,[])
    row=next(r for r in rows if r['signal_date']==days[30])
    assert row['same_close_warning_label']==1
    assert row['entry_date']==days[31] and row['label']==0


def test_future_prices_cannot_change_prior_feature_vector_and_issuer_split_is_fixed():
    data,days=packet();before=next(r for r in build_rows(data,[])[0] if r['signal_date']==days[30])
    data['split']['TEST'][days[34]]={**data['split']['TEST'][days[34]],'c':2}
    after=next(r for r in build_rows(data,[])[0] if r['signal_date']==days[30])
    assert before['x']==after['x'] and before['label']==0 and after['label']==1
    assert held_issuer('TEST')==held_issuer('TEST')


def test_strict_portfolio_does_not_place_unknown_execution_trade():
    data,days=packet()
    row={'ticker':'TEST','signal_date':'2025-09-08','entry_date':'2025-09-09',
         'raw_signal_price':5,'execution':'UNAVAILABLE'}
    result=portfolio([{**row,'score':.9}],data['raw'],data['split'],days,2025,strict=True)
    assert result['closed_trades']==0 and result['ending_balance']==100000
    conditional=portfolio([{**row,'score':.9}],data['raw'],data['split'],days,2025)
    assert conditional['closed_trades']==1 and conditional['net_profit']<0


def test_position_limit_cannot_be_bypassed_by_next_close_price_jump():
    data,days=packet()
    data['raw']['TEST']['2025-09-09']={**data['raw']['TEST']['2025-09-09'],'c':10}
    row={'ticker':'TEST','signal_date':'2025-09-08','entry_date':'2025-09-09',
         'raw_signal_price':5,'execution':'UNAVAILABLE','score':.9}
    result=portfolio([row],data['raw'],data['split'],days,2025)
    assert result['closed_trades']==0 and result['gaps']['POSITION_LIMIT_EXCEEDED_AT_FILL']==1


def test_cached_news_pagination_resumes_instead_of_stopping_at_same_pages(tmp_path,monkeypatch):
    from smg.mechanism_audit import historical_news
    calls=[]
    class Http:
        def json(self,url,params,headers):
            page=int(params.get('page_token','0'));calls.append(page)
            return {'news':[{'id':page,'headline':'known','symbols':['TEST']}],
                    'next_page_token':str(page+1) if page<2 else None}
    monkeypatch.setattr('smg.mechanism_audit.Http',Http)
    monkeypatch.setenv('ALPACA_API_KEY','fixture');monkeypatch.setenv('ALPACA_SECRET_KEY','fixture')
    first,status,requests=historical_news(['TEST'],tmp_path,budget=1,pages_per_group=1)
    assert len(first['TEST'])==1 and requests==1
    second,status,requests=historical_news(['TEST'],tmp_path,budget=2,pages_per_group=2)
    assert len(second['TEST'])==3 and calls==[0,1,2] and requests==2
    assert status[0]['status']=='PROVIDER_SEARCH_COMPLETE_NOT_EXHAUSTIVE_WEB_COVERAGE'
