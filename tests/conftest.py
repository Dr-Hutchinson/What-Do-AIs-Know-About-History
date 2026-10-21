"""Keep offline tests offline even when the preview has live credentials enabled."""
import pytest


@pytest.fixture(autouse=True)
def disable_live_in_offline_tests(monkeypatch):
    monkeypatch.setenv('LIVE_ENABLED', '0')
