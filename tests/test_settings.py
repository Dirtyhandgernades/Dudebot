from pathlib import Path
import pytest
from pydantic import ValidationError
from smg.cli import settings

def test_repository_variables_override_strategy_without_committing_threshold(monkeypatch):
    monkeypatch.setenv('SURGE_RETURN_MIN_PCT','75')
    cfg,_=settings(Path.cwd())
    assert cfg.surge_return_min_pct==75
    assert cfg.market_feed=='sip' and cfg.market_data_delay_minutes==16
    assert 'surge_return_min_pct: 12' in Path('config/strategy.yaml').read_text()
    assert cfg.ipo_low_priority_surge_max_pct==23

def test_invalid_repository_threshold_is_rejected(monkeypatch):
    monkeypatch.setenv('SURGE_RETURN_MIN_PCT','-1')
    with pytest.raises(ValidationError):settings(Path.cwd())
