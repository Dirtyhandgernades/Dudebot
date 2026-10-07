from copy import deepcopy
from smg.game_firm_replay import research_entries,interleave_years
from backtest.data_coverage import rolling_gains


def test_years_interleave_without_winner_labels_and_aliases_do_not_edit_live_rules():
    entries={'underwriter':{'Focus':['D. Boral Capital']}}
    before=deepcopy(entries);research=research_entries(entries)
    assert entries==before and 'EF Hutton LLC' in research['underwriter']['Focus']
    assert 'EF Hutton Group' not in research['underwriter']['Focus']
    items=[('b',{'file_date':'2025-01-01'}),('c',{'file_date':'2025-02-01'}),('a',{'file_date':'2021-01-01'})]
    assert [x[0] for x in interleave_years(items)]==['a','b','c']


def test_short_window_gain_is_not_season_profit():
    p={'daily_equity':[{'date':str(i),'equity':100000+i*10000} for i in range(8)]}
    r=rolling_gains(p)
    assert r['3']['best']['gain']==30000 and r['3']['windows_above_70000']==0


def test_earlier_identity_source_is_accepted_but_reused_ticker_is_quarantined():
    from backtest.balanced_packet import merge_records
    packet={'records':[{'ticker':'TEST','cik':'1','decision_at':'2024-01-01T15:00:00+00:00',
                        'source_url':'old','reasons':['VERIFIED_LISTED_FIRM_RELATIONSHIP']}],
            'first_dates':{'TEST':'2024-01-01'}}
    records=[{'ticker':'TEST','cik':'1','decision_at':'2021-01-04T15:00:00+00:00','source_url':'earlier','reasons':['VERIFIED_LISTED_FIRM_RELATIONSHIP']},
             {'ticker':'TEST','cik':'2','decision_at':'2020-01-01T15:00:00+00:00','source_url':'other company','reasons':['VERIFIED_LISTED_FIRM_RELATIONSHIP']}]
    added,earlier,conflicts=merge_records(packet,records)
    assert len(added)==1 and earlier['TEST']['after']=='2021-01-04'
    assert len(conflicts)==1 and len(packet['records'])==2
