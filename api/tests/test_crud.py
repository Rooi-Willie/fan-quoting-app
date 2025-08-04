
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# Add the project root to the Python path to allow imports from 'app'
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import crud, models, schemas
from app.database import Base

# --- Database Configuration ---

# Connection string for the source (development) database
DEV_DATABASE_URL = os.getenv("PYTEST_DATABASE_URL")
# Connection string for the destination (test) database
TEST_DATABASE_URL = os.getenv("PYTEST_DATABASE_TEST_URL")

if not DEV_DATABASE_URL or not TEST_DATABASE_URL:
    raise Exception("DATABASE_URL and DATABASE_TEST_URL must be set in your .env file")

# --- SQLAlchemy Engines and Session Factories ---
try:
    dev_engine = create_engine(DEV_DATABASE_URL)
    # Attempt to connect to the development database
    with dev_engine.connect() as connection:
        connection.execute(text("SELECT 1"))
except Exception as e:
    raise Exception(f"Could not connect to the development database at {DEV_DATABASE_URL}. Error: {e}")

try:
    test_engine = create_engine(TEST_DATABASE_URL)
    # Attempt to connect to the test database
    with test_engine.connect() as connection:
        connection.execute(text("SELECT 1"))
except Exception as e:
    raise Exception(f"Could not connect to the test database at {TEST_DATABASE_URL}. Error: {e}")

dev_engine = create_engine(DEV_DATABASE_URL)
test_engine = create_engine(TEST_DATABASE_URL)

DevSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dev_engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# --- Pytest Fixtures for Test Setup and Teardown ---

@pytest.fixture(scope="session")
def setup_test_database() -> Generator:
    """
    Fixture to set up the test database once per session.
    It creates all tables before the first test and drops them after the last test.
    """
    Base.metadata.drop_all(bind=test_engine)  # Ensure a clean slate
    Base.metadata.create_all(bind=test_engine)  # Create tables
    yield
    Base.metadata.drop_all(bind=test_engine)  # Clean up after all tests are done

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
        # List of all models to copy data from
        models_to_copy = [
            models.Material, models.LabourRate, models.GlobalSetting,
            models.Motor, models.MotorPrice, models.Component,
            models.ComponentParameter, models.FanConfiguration,
            models.FanComponentParameter
        ]

        for model in models_to_copy:
            # Read all data from the development database for the current model
            records = dev_db.query(model).all()
            if not records:
                continue

            # Convert records to dictionaries to detach them from the dev session
            records_as_dicts = [record.__dict__ for record in records]
            for r_dict in records_as_dicts:
                r_dict.pop('_sa_instance_state', None)  # Remove SQLAlchemy state

            # Bulk insert the data into the test database
            test_db.bulk_insert_mappings(model, records_as_dicts)

        yield test_db
    finally:
        transaction.rollback()
        test_db.close()
        dev_db.close()


# --- Test Cases for CRUD Functions ---

def test_get_fan_configurations(db_session: Session):
    """
    Tests retrieving all fan configurations.
    """
    source_count = db_session.query(models.FanConfiguration).count()
    if source_count == 0:
        pytest.skip("No fan configurations in source database to test.")

    fan_configs = crud.get_fan_configurations(db_session)
    assert len(fan_configs) == source_count
    assert isinstance(fan_configs[0], models.FanConfiguration)
    # Check if sorted correctly by fan_size_mm
    if len(fan_configs) > 1:
        assert fan_configs[0].fan_size_mm <= fan_configs[1].fan_size_mm

def test_get_fan_configuration(db_session: Session):
    """
    Tests retrieving a single fan configuration by a valid ID.
    """
    first_config = db_session.query(models.FanConfiguration).first()
    if not first_config:
        pytest.skip("No fan configurations in source database to test.")

    fan_config = crud.get_fan_configuration(db_session, fan_config_id=first_config.id)
    assert fan_config is not None
    assert fan_config.id == first_config.id
    assert fan_config.uid == first_config.uid

def test_get_non_existent_fan_configuration(db_session: Session):
    """
    Tests retrieving a fan configuration that does not exist.
    """
    fan_config = crud.get_fan_configuration(db_session, fan_config_id=99999)
    assert fan_config is None

def test_get_available_components(db_session: Session):
    """
    Tests retrieving available components for a fan.
    """
    config_with_components = db_session.query(models.FanConfiguration).filter(
        models.FanConfiguration.available_components.isnot(None)
    ).first()
    
    if not config_with_components:
        pytest.skip("No fan configuration with available components to test.")

    components = crud.get_available_components(db_session, fan_config_id=config_with_components.id)
    assert len(components) == len(config_with_components.available_components)
    if components:
        assert isinstance(components[0], models.Component)

def test_get_motors(db_session: Session):
    """
    Tests retrieving all motors with their latest prices.
    """
    source_motors_with_price = db_session.query(models.Motor).join(models.MotorPrice).count()
    if source_motors_with_price == 0:
        pytest.skip("No motors with prices in source database to test.")

    motors = crud.get_motors(db_session)
    assert len(motors) == source_motors_with_price
    assert isinstance(motors[0], schemas.MotorWithLatestPrice)
    assert motors[0].latest_price_date is not None

def test_get_materials(db_session: Session):
    """
    Tests retrieving all materials.
    """
    source_count = db_session.query(models.Material).count()
    if source_count == 0:
        pytest.skip("No materials in source database to test.")
        
    materials = crud.get_materials(db_session)
    assert len(materials) == source_count
    assert isinstance(materials[0], models.Material)

def test_get_labour_rates(db_session: Session):
    """
    Tests retrieving all labour rates.
    """
    source_count = db_session.query(models.LabourRate).count()
    if source_count == 0:
        pytest.skip("No labour rates in source database to test.")

    labour_rates = crud.get_labour_rates(db_session)
    assert len(labour_rates) == source_count
    assert isinstance(labour_rates[0], models.LabourRate)

def test_get_global_settings(db_session: Session):
    """
    Tests retrieving all global settings.
    """
    source_count = db_session.query(models.GlobalSetting).count()
    if source_count == 0:
        pytest.skip("No global settings in source database to test.")

    settings = crud.get_global_settings(db_session)
    assert len(settings) == source_count
    assert isinstance(settings[0], models.GlobalSetting)

def test_get_rates_and_settings(db_session: Session):
    """
    Tests consolidating all rates and settings into a dictionary.
    """
    if db_session.query(models.GlobalSetting).count() == 0:
        pytest.skip("No global settings in source database to test.")

    rates_dict = crud.get_rates_and_settings(db_session)
    assert isinstance(rates_dict, dict)
    assert len(rates_dict) > 0
