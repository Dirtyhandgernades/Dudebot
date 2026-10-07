"""Prior-data-only advisory exposure limits; no orders or loss guarantees."""
import math

POLICY={'id':'bounded-short-exposure-v1','max_position_fraction':.10,
        'max_gross_fraction':.60,'shock_loss_fraction':.02,'shock_floor':.25,
        'range_multiplier':2.,'range_lookback_sessions':5,
        'target_ceiling':20000,'cooldown_sessions':3}


def range_fraction(history):
    if not history or any(not all(isinstance(r.get(k),(int,float)) and
        math.isfinite(r[k]) for k in ('h','l','c')) or r['c']<=0 or r['h']<r['l'] for r in history):return None
    return max((r['h']-r['l'])/r['c'] for r in history)


def budget(equity,available,target,observed_range=None,reserved=0,policy=None):
    spec=policy or POLICY
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0
           for v in (equity,available,target,reserved)):raise ValueError('Invalid exposure assumptions')
    valid=isinstance(observed_range,(int,float)) and math.isfinite(observed_range) and observed_range>=0
    # Unknown range gets a 100% adverse-move stress, never an optimistic zero.
    shock=max(spec['shock_floor'],spec['range_multiplier']*observed_range) if valid else 1.
    gross_room=max(0,equity*spec['max_gross_fraction']-reserved)
    ceiling=max(0,min(target,spec['target_ceiling'],equity*spec['max_position_fraction'],
                      equity*spec['shock_loss_fraction']/shock,available,gross_room))
    return {'policy_id':spec['id'],'ceiling':ceiling,'adverse_move_stress':shock,
            'stress_loss_budget':equity*spec['shock_loss_fraction'],
            'modeled_adverse_loss':ceiling*shock,'reserved':reserved,
            'range_status':'KNOWN_PRIOR_RANGE' if valid else 'UNKNOWN_RANGE_100_PERCENT_STRESS',
            'loss_is_capped':False}


def reserve(store,ticker,day,capital,sessions,policy_id):
    """Reserve quoted advisory capacity for three sessions, not real holdings.

    Claims survive failed/ambiguous delivery. Repeated ticker/day proposals do
    not create additional room. Unrecognized dates stay reserved.
    """
    key='paper_exposure_reservations';rows=store.get(key,{}) or {};index={d:i for i,d in enumerate(sessions)}
    live={k:r for k,r in rows.items() if
          (day<=r['expires_on'] if r.get('expires_on') else
           r['day'] not in index or day not in index or index[day]<=index[r['day']]+3)}
    claim=policy_id+':'+day+':'+ticker
    if capital is not None and claim not in live:
        from .market import calendar
        cal=calendar(int(day[:4]));expires=day
        for _ in range(3):expires=str(cal.next_session(expires).date())
        live[claim]={'ticker':ticker,'day':day,'expires_on':expires,'capital':capital,'policy_id':policy_id}
        store.put(key,live)
    return sum(r['capital'] for r in live.values()),next((r for r in live.values() if r['ticker']==ticker),None)
