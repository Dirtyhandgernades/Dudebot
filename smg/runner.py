from datetime import timedelta
from .rules import structural,evaluate
from .market import calculate,snapshot_window
from .firm_first import firm_structure,evaluate_firm_first
from .game_rules import NasdaqMarketCaps

class Scanner:
    def __init__(self,market,halts,cfg,entities,store,market_caps=None):
        self.market=market;self.halts=halts;self.cfg=cfg;self.entities=entities;self.store=store;self.bar_cache={}
        self.market_caps=market_caps or (NasdaqMarketCaps(market.http) if hasattr(market,'http') else None)
    def scan(self,candidates,now):
        results=[]
        structure=firm_structure if self.cfg.screening_profile=='firm_first' else structural
        assess=evaluate_firm_first if self.cfg.screening_profile=='firm_first' else evaluate
        for c in candidates:
            r=structure(c,self.cfg,self.entities,now)
            if r.status!='STRUCTURAL_MATCH':results.append(r);continue
            halt=self.halts.check(c.ticker,now)
            if halt.status!='CLEAR':results.append(assess(c,self.cfg,self.entities,now,halt=halt));continue
            try:
                effective_now=now-timedelta(minutes=self.cfg.market_data_delay_minutes)
                if not snapshot_window(effective_now):raise ValueError('MARKET_CLOSED')
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
            except Exception as exc:
                r.status='REVIEW_REQUIRED';r.reasons.append(str(exc) if isinstance(exc,(ValueError,RuntimeError)) else type(exc).__name__)
            self.store.put('evaluation:'+c.key,r.model_dump(mode='json'));results.append(r)
        return results
