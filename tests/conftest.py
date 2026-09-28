import pytest

from shared.config import settings as settings_mod
from shared.infrastructure.database import db_models


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    """Fresh data dir + SQLite DB + JWT secret per test."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("JWT_SECRET", "test-secret-not-for-prod-0123456789abcdef")
    settings_mod.get_settings.cache_clear()
    db_models._engine = None
    yield tmp_path
    db_models._engine = None
    settings_mod.get_settings.cache_clear()