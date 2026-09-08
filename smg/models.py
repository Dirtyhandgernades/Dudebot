from __future__ import annotations
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class Config(Strict):
    screening_profile: Literal['strict','firm_first'] = 'strict'
    surge_return_min_pct: float | None = Field(default=None, gt=0)
    ipo_low_priority_surge_max_pct: float | None = Field(default=None, gt=0)
    ipo_max_age_years: int = Field(default=3, ge=1)
    ipo_focus_days: list[int] = [30, 100]
    ipo_preferred_age_years: int = 1
    ipo_operations_countries: list[str] = ['CN']
    offer_gross_usd_min: float = 15_000_000
    offer_gross_usd_max: float = 30_000_000
    offer_price_usd_min: float = 4
    offer_price_usd_max: float = 10
    rvol_min: float = Field(default=1, ge=1)
    exclude_halted: Literal[True] = True
    exclude_acquisition_corps: Literal[True] = True
    exclude_five_letter_tickers: Literal[True] = True
    entity_match_min: int = Field(default=1, ge=1)
    rvol_target_sessions: int = 60
    rvol_min_sessions: int = 20
    monthly_return_sessions: int = 21
    max_snapshot_age_seconds: int = 300
    direct_offering_backfill_days: int = 30
    direct_offering_require_monthly_surge: bool = False
    notification_timezone: Literal['fixed_UTC_minus_08', 'America/Los_Angeles'] = 'fixed_UTC_minus_08'
    notification_time: Literal['12:00'] = '12:00'
    send_window_seconds: int = Field(default=60, ge=1, le=60)
    no_match_message: Literal[False] = False
    parser_max_filings_per_run: int = Field(default=100, ge=1)
    filings_max_downloads_per_run: int = Field(default=150, ge=1)
    market_feed: Literal['sip','iex'] = 'sip'
    market_data_delay_minutes: int = Field(default=16, ge=0, le=30)
    state_branch: str = 'smg-state'

class Evidence(Strict):
    url: str
    filed_at: date
    quote: str = Field(min_length=10)
    document_sha256: str

class EntityMatch(Strict):
    name: str
    role: Literal['underwriter','placement_agent','auditor','counsel']
    relationship: Literal['transaction','current','historical']
    evidence: Evidence

class Candidate(Strict):
    pipeline: Literal['RECENT_IPO','DIRECT_OFFERING','FIRM_WATCH']
    cik: str
    ticker: str
    name: str
    event_id: str  # issuer + economic transaction, NOT article identifier
    exchange: str
    operations_country: str | None
    ipo_date: date | None
    event_date: date
    status: Literal['priced','closed','canceled','unknown']
    security_type: str | None
    is_acquisition_corp: bool | None
    offer_price: float | None
    offer_gross: float | None
    currency: str | None
    base_shares: float | None
    terms_unambiguous: bool
    matches: list[EntityMatch]
    evidence: dict[str, Evidence]
    notes: list[str] = []
    reviewed_at: datetime

    @property
    def key(self):
        return f'{self.pipeline}:{self.cik}:{self.event_id}'

class Bar(Strict):
    start: datetime
    close: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    volume: float = Field(ge=0)

class Snapshot(Strict):
    asof: datetime
    price_time: datetime
    price: float
    monthly_return: float | None
    one_day_return: float | None
    five_day_return: float | None
    since_first_close_return: float | None = None
    drawdown_pct: float
    rvol: float | None
    rvol20: float | None
    baseline_sessions: int
    cumulative_volume: float
    baseline_volume: float | None
    source_url: str
    flags: list[str] = []
    feed: str = 'synthetic'
    declared_delay_minutes: int = 0

class HaltCheck(Strict):
    checked_at: datetime
    status: Literal['CLEAR','HALTED','UNKNOWN']
    reason: str
    source_url: str

class Evaluation(Strict):
    candidate: Candidate
    status: str
    reasons: list[str]
    snapshot: Snapshot | None = None
    halt: HaltCheck | None = None
    rank: list[float] = []
    matches: list[dict] = []
