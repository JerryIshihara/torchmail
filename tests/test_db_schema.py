"""Schema/model tests for MVP database tables."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from search_engine import db as search_db


def test_professor_model_exposes_new_scrape_url_fields():
    professor_columns = search_db.Professor.__table__.columns
    assert "homepage_url" in professor_columns
    assert "lab_url" in professor_columns


def test_hiring_signal_model_is_registered_with_expected_columns():
    assert "lab_hiring_signals" in search_db.Base.metadata.tables

    signal_columns = search_db.LabHiringSignal.__table__.columns
    assert "professor_id" in signal_columns
    assert "hiring_url" in signal_columns
    assert "hiring_paragraph" in signal_columns
    assert "keywords_matched" in signal_columns
    assert "expires_at" in signal_columns
    assert "is_active" in signal_columns


def test_hiring_signal_expiry_default_is_ttl_based(monkeypatch):
    monkeypatch.setattr(search_db.config, "HIRING_SIGNAL_TTL_DAYS", 7)
    default_callable = search_db.LabHiringSignal.__table__.columns["expires_at"].default.arg

    before = datetime.now(timezone.utc)
    expires_at = default_callable(None)
    after = datetime.now(timezone.utc)

    expected_min = before + timedelta(days=7) - timedelta(seconds=1)
    expected_max = after + timedelta(days=7) + timedelta(seconds=1)
    assert expected_min <= expires_at <= expected_max


def test_init_db_calls_create_all(monkeypatch):
    class DummyEngine:
        pass

    dummy_engine = DummyEngine()
    calls: list[object] = []

    monkeypatch.setattr(search_db, "get_engine", lambda: dummy_engine)
    monkeypatch.setattr(search_db.Base.metadata, "create_all", lambda engine: calls.append(engine))

    search_db.init_db()

    assert calls == [dummy_engine]
