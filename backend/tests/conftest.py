"""Test fixtures.

Parser unit tests (test_cv_parser.py, test_jd_parser.py) need no fixtures from
here and run fully offline — no Postgres, no network.

API tests (test_api_*.py) use `client`, which requires a running Postgres
(docker compose up -d postgres) since they exercise the real DB + pgvector
column type.
"""

import os

os.environ.setdefault("APP_ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import Base, SessionLocal, engine, get_db
from app.dependencies import get_embedder, get_llm
from app.main import app
from app.services.embeddings import FakeHashEmbedding
from app.services.llm_client import MockLLMProvider


@pytest.fixture(scope="session")
def _schema_ready():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def db_session(_schema_ready):
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        with engine.connect() as conn:
            conn.execute(
                text(
                    "TRUNCATE candidates, jobs, audit_logs, llm_call_logs, score_results "
                    "RESTART IDENTITY CASCADE"
                )
            )
            conn.commit()


@pytest.fixture
def mock_llm():
    return MockLLMProvider(responses=[])


@pytest.fixture
def client(_schema_ready, mock_llm):
    def _get_db_override():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_llm] = lambda: mock_llm
    app.dependency_overrides[get_embedder] = lambda: FakeHashEmbedding()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    with engine.connect() as conn:
        conn.execute(
            text(
                "TRUNCATE candidates, jobs, audit_logs, llm_call_logs, score_results "
                "RESTART IDENTITY CASCADE"
            )
        )
        conn.commit()
