from backtest.obsidian_cover_review import review


def test_review_directions_and_mandatory_exit():
    down = [dict(c=p,h=p+1) for p in (8,7,6)]
    assert review('TIME_LIMIT',down)=='CONTINUATION_REVIEW'
    assert review('TIME_LIMIT',down[::-1])=='REVERSAL_REVIEW'
    assert review('STOP_SIGNAL_PREVIOUS_CLOSE',down)=='PRESERVE_EXISTING_EXIT'
    assert review('TIME_LIMIT',down[:2])=='INSUFFICIENT_DATA'
    assert review('TIME_LIMIT',[down[0],down[2],down[1]])=='MIXED_EVIDENCE'
