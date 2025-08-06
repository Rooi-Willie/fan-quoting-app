import pytest
from sqlalchemy.orm import Session
from app import crud, models, schemas

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