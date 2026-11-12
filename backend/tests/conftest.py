import os
import tempfile

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp()

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def db():
    Base.metadata.create_all(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    def _override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_user(client, **overrides):
    payload = {
        "business_name": "Test EOOD",
        "eik_bulstat": "123456789",
        "vat_number": "BG123456789",
        "user_name": "Test User",
        "email": "test@example.com",
        "password": "secure123",
    }
    payload.update(overrides)
    return client.post("/api/auth/register", json=payload)


def login_user(client, email="test@example.com", password="secure123"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth_header(client, email="test@example.com", password="secure123"):
    resp = login_user(client, email, password)
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
