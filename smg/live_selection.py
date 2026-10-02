"""Bounded live scan selection with explicit firm-watch coverage."""

def select(candidates,preferred,cfg):
    order={symbol:i for i,symbol in enumerate(preferred or [])}
    firm=[c for c in candidates if c.pipeline=='FIRM_WATCH']
    broad=[c for c in candidates if c.pipeline=='VOLATILITY_WATCH']
    strict=[c for c in candidates if c.pipeline not in {'FIRM_WATCH','VOLATILITY_WATCH'}]
    # Firm evidence is the user's primary research lane. Keep the broad lane
    # small, but never turn a firm match into a trade without execution gates.
    firm=sorted(firm,key=lambda c:(order.get(c.ticker,len(order)),
        c.is_acquisition_corp is None,-c.reviewed_at.timestamp(),c.ticker))[:cfg.firm_live_shortlist_size]
    broad=sorted(broad,key=lambda c:(-c.reviewed_at.timestamp(),c.ticker))[:cfg.broad_shortlist_size]
    strict=sorted(strict,key=lambda c:(-c.reviewed_at.timestamp(),c.ticker))[:cfg.strict_live_shortlist_size]
    return firm+broad+strict,{'firm':len(firm),'volatility':len(broad),'strict':len(strict)}
