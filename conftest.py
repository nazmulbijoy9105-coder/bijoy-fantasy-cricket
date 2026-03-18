"""conftest.py — pytest configuration."""
import os
import pytest

# Use an in-memory/temp DB for tests
os.environ["DATABASE_PATH"] = ":memory:"

@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    from database.migrate import run
    run()
