from datetime import datetime,timedelta
from .rules import structural,evaluate
from .market import calculate,snapshot_window
from .firm_first import firm_structure,evaluate_firm_first
from .game_rules import NasdaqMarketCaps

class Scanner:
    def __init__(self,market,halts,cfg,entities,store,market_caps=None):
        self.market=market;self.halts=halts;self.cfg=cfg;self.entities=entities;self.store=store;self.bar_cache={}
        self.market_caps=market_caps or (NasdaqMarketCaps(market.http) if hasattr(market,'http') else None)
        self.asset_cache={}
    def _ranking_context(self,ticker,now):
        context={}
        for kind in ['finra_short_volume','sentiment']:
            row=self.store.latest_observation(kind,ticker)
            if row:
                try:age=(now-datetime.fromisoformat(row['observed_at'])).total_seconds()
                except (ValueError,TypeError):age=None
                context[kind]={**row,'age_seconds':age}
        return context
    def _borrow(self,ticker):
        if ticker not in self.asset_cache:
            from .shortability import current_assets
            self.asset_cache[ticker]=current_assets(self.market.http,[ticker],getattr(self.market,'headers',{}))['assets'][ticker]
        return self.asset_cache[ticker]
    def scan(self,candidates,now):
        results=[]
        for c in candidates:
            if c.pipeline=='VOLATILITY_WATCH':
                from .volatility import volatility_structure,evaluate_volatility
                structure,assess=volatility_structure,evaluate_volatility
            else:
                structure=firm_structure if self.cfg.screening_profile=='firm_first' else structural
                assess=evaluate_firm_first if self.cfg.screening_profile=='firm_first' else evaluate
            r=structure(c,self.cfg,self.entities,now)
            if r.status!='STRUCTURAL_MATCH':results.append(r);continue
            halt=self.halts.check(c.ticker,now)
            if halt.status!='CLEAR':results.append(assess(c,self.cfg,self.entities,now,halt=halt));continue
            try:
                effective_now=now-timedelta(minutes=self.cfg.market_data_delay_minutes)
                if not snapshot_window(effective_now):raise ValueError('MARKET_CLOSED')
                # Borrow is a cheap point-in-time asset lookup. Fail closed
                # here so hard-to-borrow names never trigger the much larger
                # 150-day minute-bar download.
                borrow=None
                if self.cfg.short_alerts_require_borrow:
                    from .shortability import executable_short
                    borrow=self._borrow(c.ticker)
                    if not executable_short(borrow):
                        r.status='REVIEW_REQUIRED';r.reasons.append('CURRENT_BORROW_NOT_EXECUTABLE');r.shortability=borrow
                        self.store.put('evaluation:'+c.key,r.model_dump(mode='json'));results.append(r);continue
                # No cached vendor minute bars across days: all adjustments are as of this run.
                cache_key=(c.ticker,now.date())
                if cache_key in self.bar_cache:
                    fresh=self.market.bars(c.ticker,now.date(),effective_now)
                    bars=[b for b in self.bar_cache[cache_key] if b.start.date()<now.date()]+fresh
                else:
                    bars=self.market.bars(c.ticker,now.date()-timedelta(days=150),effective_now)
                    self.bar_cache[cache_key]=bars
                snapshot=calculate(bars,effective_now,self.cfg,'https://data.alpaca.markets/v2/stocks/bars?symbols='+c.ticker+'&feed='+self.cfg.market_feed,c.ipo_date)
                snapshot.feed=self.cfg.market_feed;snapshot.declared_delay_minutes=self.cfg.market_data_delay_minutes
                if self.market_caps:self.market_caps.apply(c,snapshot,now)
                if self.cfg.market_data_delay_minutes:snapshot.flags.append('DELAYED_MARKET_DATA')
                if any('ads ratio' in n.lower() or 'ticker change' in n.lower() for n in c.notes):snapshot.flags.append('CORPORATE_ACTION_REVIEW')
                r=assess(c,self.cfg,self.entities,now,snapshot,halt)
                if r.status=='QUALIFIED':
                    r.signal_side=self.cfg.live_signal_side
                    r.ranking_evidence=self._ranking_context(c.ticker,now)
                    if self.cfg.short_alerts_require_borrow:r.shortability=borrow
                    # Context changes ordering only. Missing context never creates
                    # or suppresses an otherwise eligible trade.
                    finra=(r.ranking_evidence.get('finra_short_volume') or {}).get('value',{})
                    sentiment=(r.ranking_evidence.get('sentiment') or {}).get('value',{})
                    r.rank += [-float(finra.get('short_volume_ratio') or 0),float(sentiment.get('score') or 0)]
            except Exception as exc:
                r.status='REVIEW_REQUIRED';r.reasons.append(str(exc) if isinstance(exc,(ValueError,RuntimeError)) else type(exc).__name__)
            self.store.put('evaluation:'+c.key,r.model_dump(mode='json'));results.append(r)
        return results
