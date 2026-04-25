from collections.abc import Iterator

import pytest
from chiron_backend.api.main import app
from chiron_backend.api.store import RUNS
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clear_runs() -> Iterator[None]:
    RUNS.clear()
    yield
    RUNS.clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
