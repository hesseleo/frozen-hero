"""Shared fixtures and hardware stubs for frozen-hero tests.

RPi.GPIO, picamera2, and pyzbar are Pi-only packages.  They must be
injected into sys.modules *before* any frozen_hero module is imported,
so this file does that at module level — pytest loads conftest.py first.
"""

import sqlite3
import sys
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Stub Pi-only packages
# ---------------------------------------------------------------------------
# `import RPi.GPIO as GPIO` in scanner.py calls __import__("RPi.GPIO") which
# returns the top-level "RPi" package, then does `GPIO = RPi_mod.GPIO`.
# So we need RPi_mock.GPIO to be the same object as sys.modules["RPi.GPIO"].
_gpio_mock = MagicMock(name="RPi.GPIO")
_rpi_mock = MagicMock(name="RPi")
_rpi_mock.GPIO = _gpio_mock
sys.modules.setdefault("RPi", _rpi_mock)
sys.modules.setdefault("RPi.GPIO", _gpio_mock)

sys.modules.setdefault("picamera2", MagicMock())

_pyzbar_stub = MagicMock()
sys.modules.setdefault("pyzbar", _pyzbar_stub)
sys.modules.setdefault("pyzbar.pyzbar", _pyzbar_stub)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
from frozen_hero import config  # noqa: E402 — must come after sys.modules setup


def _create_schema(path):
    con = sqlite3.connect(path)
    con.execute(
        "CREATE TABLE freezer("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "row_one TEXT, row_two TEXT, category TEXT, date DATE)"
    )
    con.commit()
    con.close()


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    """Isolated SQLite database for each test."""
    db_file = tmp_path / "test.db"
    _create_schema(db_file)
    monkeypatch.setattr(config, "DB_PATH", db_file)
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
