
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import sys

# Add the project root to the Python path to allow imports from 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import models
from app.database import Base

# --- Database Configuration ---
DEV_DATABASE_URL = os.getenv("PYTEST_DATABASE_URL")
TEST_DATABASE_URL = os.getenv("PYTEST_DATABASE_TEST_URL")

if not DEV_DATABASE_URL or not TEST_DATABASE_URL:
    raise Exception("PYTEST_DATABASE_URL and PYTEST_DATABASE_TEST_URL must be set as environment variables.")

# --- SQLAlchemy Engines and Session Factories ---
try:
    dev_engine = create_engine(DEV_DATABASE_URL)
    with dev_engine.connect() as connection:
        connection.execute(text("SELECT 1"))
except Exception as e:
    raise Exception(f"Could not connect to the development database. Error: {e}")

try:
    test_engine = create_engine(TEST_DATABASE_URL)
    with test_engine.connect() as connection:
        connection.execute(text("SELECT 1"))
except Exception as e:
    raise Exception(f"Could not connect to the test database. Error: {e}")

DevSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dev_engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# --- Pytest Fixtures for Test Setup and Teardown ---

@pytest.fixture(scope="session")
def setup_test_database() -> Generator:
    """
    Fixture to set up the test database once per session.
    It creates all tables before the first test and drops them after the last test.
    """
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def db_session(setup_test_database) -> Generator[Session, None, None]:
    """
    Fixture to provide a clean, data-populated database session for each test function.
    This fixture will:
    1. Connect to the development database to read the data.
    2. Copy all data from relevant tables into the test database within a transaction.
    3. Yield a session connected to the test database for the test to use.
    4. Rollback the transaction to ensure the next test starts with a fresh copy.
    """
    dev_db = DevSessionLocal()
    test_db = TestingSessionLocal()
    transaction = test_db.begin()

    try:
        models_to_copy = [
            models.Material, models.LabourRate, models.GlobalSetting,
            models.Motor, models.MotorPrice, models.Component,
            models.ComponentParameter, models.FanConfiguration,
            models.FanComponentParameter
        ]

        for model in models_to_copy:
            records = dev_db.query(model).all()
            if not records:
                continue

            records_as_dicts = [record.__dict__ for record in records]
            for r_dict in records_as_dicts:
                r_dict.pop('_sa_instance_state', None)

            test_db.bulk_insert_mappings(model, records_as_dicts)

        yield test_db
    finally:
        transaction.rollback()
        test_db.close()
        dev_db.close()
