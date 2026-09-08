from datetime import datetime,timedelta,timezone
import pandas as pd
import pytest
from smg.market import calculate,calendar,session_bounds
from smg.models import Bar,Config
UTC=timezone.utc
NOW=datetime(2026,9,8,19,0,0,tzinfo=UTC)

def bars():
    cal=calendar(2026);days=[x.date() for x in cal.sessions_in_range('2026-05-01','2026-09-04')][-60:]
    out=[]
    # Two bars represent sparse but valid trading: 1,000 before the cutoff, 9,000 after.
    for day in days:
        o,c=session_bounds(day)
        out.append(Bar(start=o,close=10,high=10,low=10,volume=1000))
        out.append(Bar(start=c-timedelta(minutes=1),close=10,high=10,low=10,volume=9000))
    o,_=session_bounds(NOW.date())
    out.extend([Bar(start=o,close=20,high=20,low=20,volume=500),Bar(start=NOW-timedelta(minutes=1),close=20,high=20,low=20,volume=1500)])
    return out,days

def test_same_time_rvol_not_full_day():
    rows,days=bars();s=calculate(rows,NOW,Config(),'https://example.com/bars',days[0])
    assert s.rvol==2 and s.baseline_volume==1000 and s.monthly_return==100

def test_future_partial_premarket_ignored():
    rows,days=bars();o,_=session_bounds(NOW.date())
    for stamp in [NOW,NOW+timedelta(minutes=1),o-timedelta(minutes=1)]:rows.append(Bar(start=stamp,close=1000,high=1000,low=1000,volume=9e6))
    s=calculate(rows,NOW,Config(),'https://example.com',days[0]);assert s.rvol==2 and s.price==20

def test_missing_session_not_silently_removed():
    rows,days=bars();rows=[b for b in rows if b.start.date()!=days[10]]
    s=calculate(rows,NOW,Config(),'https://example.com',days[0])
    assert 'MISSING_SESSION_DATA' in s.flags

def test_short_history_has_no_fabricated_month():
    rows,days=bars();rows=[b for b in rows if b.start.date()>=days[-10]]
    s=calculate(rows,NOW,Config(),'https://example.com',days[-10])
    assert s.monthly_return is None and s.rvol is None and s.baseline_sessions==10

def test_market_holiday_closed():
    rows,_=bars()
    with pytest.raises(ValueError,match='MARKET_CLOSED'):calculate(rows,datetime(2026,9,7,19,tzinfo=UTC),Config(),'x')
