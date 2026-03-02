"""Shared fixtures and hardware stubs for frozen-hero tests.

lgpio, picamera2, and pyzbar are Pi-only packages.  They must be
injected into sys.modules *before* any frozen_hero module is imported,
so this file does that at module level — pytest loads conftest.py first.
"""

import sys
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Stub Pi-only packages
# ---------------------------------------------------------------------------
_lgpio_mock = MagicMock(name="lgpio")
_lgpio_mock.gpiochip_open.return_value = 0
_lgpio_mock.callback.return_value = MagicMock()
sys.modules.setdefault("lgpio", _lgpio_mock)

sys.modules.setdefault("picamera2", MagicMock())

_pyzbar_stub = MagicMock()
sys.modules.setdefault("pyzbar", _pyzbar_stub)
sys.modules.setdefault("pyzbar.pyzbar", _pyzbar_stub)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
from frozen_hero import config, db  # noqa: E402 — must come after sys.modules setup


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    """Isolated SQLite database for each test."""
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(config, "DB_PATH", db_file)
    db.init_db()
    return db_file


@pytest.fixture()
def app(tmp_db, monkeypatch):
    """Flask test app with an isolated DB and label printing mocked out."""
    monkeypatch.setattr("frozen_hero.label.print_label", MagicMock())
    from frozen_hero.app import create_app

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()
