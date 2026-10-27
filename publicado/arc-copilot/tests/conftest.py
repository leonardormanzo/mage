from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.session import Base, get_db
from app.main import app
from app.seed import seed_demo


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    with tempfile.TemporaryDirectory() as folder:
        database_path = Path(folder) / "test.db"
        engine = create_engine(
            f"sqlite:///{database_path.as_posix()}", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(engine)
        testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with testing_session() as session:
            seed_demo(session)
            yield session
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def login(client: TestClient, email: str = "trabalhador@arc.local") -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": "ArcDemo123!"})
    assert response.status_code == 200
    return client.get("/api/me").json()
