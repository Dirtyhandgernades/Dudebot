"""Use fully completed one-minute bars and exchange sessions, not clock-day averages."""
from datetime import datetime, timedelta, timezone
from statistics import mean
from functools import lru_cache
import pandas as pd
import exchange_calendars as xcals
from .models import Bar, Snapshot
UTC=timezone.utc

@lru_cache(maxsize=12)
def calendar(year):
    return xcals.get_calendar('XNYS', start=f'{year-4}-01-01', end=f'{year+1}-12-31')

def session_bounds(day):
    cal=calendar(day.year)
    label=pd.Timestamp(day)
    if not cal.is_session(label): return None
    return cal.session_open(label).to_pydatetime(),cal.session_close(label).to_pydatetime()

def is_open(now):
    # UTC dates and U.S. session dates coincide during the regular session.
    bounds=session_bounds(now.date())
    return bool(bounds and bounds[0] <= now < bounds[1])

def snapshot_window(now):
    bounds=session_bounds(now.date())
    return bool(bounds and bounds[0] <= now < bounds[1]+timedelta(minutes=5))

def calculate(bars: list[Bar], now, cfg, source_url, ipo_date=None):
    if now.tzinfo is None: raise ValueError('Timezone-aware time required')
    if not snapshot_window(now): raise ValueError('MARKET_CLOSED')
    bounds=session_bounds(now.date()); open_time=bounds[0]
    cutoff=min(now.replace(second=0,microsecond=0),bounds[1])
    minutes=int((cutoff-open_time).total_seconds()/60)
    if minutes <= 0: raise ValueError('NO_COMPLETED_SESSION_MINUTES')
    # Deduplicate bars. Strictly ignore partial/future bars and non-session trades.
    by_day={}
    for bar in sorted({b.start:b for b in bars}.values(), key=lambda x:x.start):
        if bar.start.tzinfo is None: raise ValueError('Naive bar timestamp')
        day=bar.start.astimezone(UTC).date()
        b=session_bounds(day)
        if not b or not b[0] <= bar.start < b[1] or bar.start+timedelta(minutes=1)>cutoff: continue
        by_day.setdefault(day,[]).append(bar)
    current=by_day.get(now.date(),[])
    if not current: raise ValueError('NO_CURRENT_SESSION_BARS')
    cal=calendar(now.year)
    previous=[s.date() for s in cal.sessions_in_range(pd.Timestamp(now.date()-timedelta(days=150)),pd.Timestamp(now.date()-timedelta(days=1)))]
    if ipo_date: previous=[d for d in previous if d>=ipo_date]
    expected=[day for day in previous if (session_bounds(day)[1]-session_bounds(day)[0]).total_seconds()/60 >= minutes][-cfg.rvol_target_sessions:]
    flags=[] if is_open(now) else ['SESSION_JUST_CLOSED']; volumes=[]
    for day in expected:
        b=by_day.get(day)
        # Entirely absent sessions are not silently excluded from the average.
        if not b:
            flags.append('MISSING_SESSION_DATA'); continue
        end=session_bounds(day)[0]+timedelta(minutes=minutes)
        volumes.append(sum(v.volume for v in b if v.start+timedelta(minutes=1)<=end))
    count=len(volumes); base=mean(volumes) if volumes else None
    total=sum(b.volume for b in current)
    rvol=total/base if base and base>0 and count>=cfg.rvol_min_sessions else None
    short=mean(volumes[-20:]) if len(volumes)>=20 else None
    price=current[-1].close
    def ret(n):
        if len(previous)<n: return None
        rows=by_day.get(previous[-n]); return (price/rows[-1].close-1)*100 if rows else None
    monthly=ret(cfg.monthly_return_sessions)
    if monthly is None: flags.append('SHORT_HISTORY')
    if count<cfg.rvol_target_sessions: flags.append('SHORT_BASELINE')
    window_days=set(previous[-cfg.monthly_return_sessions:]+[now.date()])
    high=max(b.high for day, rows in by_day.items() if day in window_days for b in rows)
    first=by_day.get(ipo_date) if ipo_date else None
    return Snapshot(asof=now,price_time=current[-1].start,price=price,monthly_return=monthly,
        one_day_return=ret(1),five_day_return=ret(5),since_first_close_return=(price/first[-1].close-1)*100 if first and ipo_date<now.date() else None,
        drawdown_pct=(price/high-1)*100,rvol=rvol,rvol20=total/short if short and short>0 else None,
        baseline_sessions=count,cumulative_volume=total,baseline_volume=base,source_url=source_url,flags=sorted(set(flags)))
