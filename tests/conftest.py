import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import Base, make_engine, make_session_factory
from app.main import create_app
from app.providers import MockProvider
from app.seed import seed


@pytest.fixture
def session():
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    s = make_session_factory(engine)()
    seed(s)
    yield s
    s.close()


@pytest.fixture
def provider():
    return MockProvider("Test Store")


@pytest.fixture
def client():
    app = create_app(Settings(llm_provider="mock", database_url="sqlite://", store_name="Test Store"))
    with TestClient(app) as c:
        yield c
