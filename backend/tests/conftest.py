"""Pytest Configuration and Shared Fixtures."""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.models.base import Base
from backend.app.services.persistence.database import get_db
import backend.app.main

# Mock init_db during testing so lifespan doesn't touch production SQLite
backend.app.main.init_db = lambda: None

TEST_DB_PATH = "test_literature_review.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///./{TEST_DB_PATH}"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database_tables():
    """Initializes tables in test database once per session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    # Cleanup after entire test session
    try:
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    except Exception:
        pass


@pytest.fixture(autouse=True)
def apply_dependency_overrides():
    """Ensures FastAPI app uses the test database session for all endpoints."""
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
