import pytest
from sqlalchemy.orm import Session
from app.logic import calculation_engine
from app import models, crud

# --- Test for the Helper Function using real data ---

@pytest.mark.parametrize("component_name, expected_diameter, expected_length", [
    ("Casing", 762, None),  # Assuming Casing uses HUB_DIAMETER
    ("Inlet Cone", 982, 206.7), # CONICAL_60_DEG and CONICAL_15_DEG
    ("Screen Inlet", 952.5, None) # HUB_DIAMETER_X_1_25
])
def test_resolve_formulaic_parameters_with_real_data(
    db_session: Session, component_name: str, expected_diameter: float, expected_length: float
):
    """Tests the parameter resolution using data from the database."""
    # --- Setup ---
    fan_config = db_session.query(models.FanConfiguration).filter_by(fan_size_mm=762).first()
    component = db_session.query(models.Component).filter_by(name=component_name).first()
    params = crud.get_parameters_for_calculation(db_session, fan_config.id, [component.id])[0]

    # --- Execute ---
    resolved = calculation_engine._resolve_formulaic_parameters(
        hub_size=fan_config.hub_size_mm,
        fan_size=fan_config.fan_size_mm,
        params=params
    )

    # --- Assert ---
    if expected_diameter:
        assert pytest.approx(resolved['diameter_mm'], 0.1) == expected_diameter
    if expected_length:
        assert pytest.approx(resolved['length_mm'], 0.1) == expected_length

# --- Placeholder for Calculator and Orchestrator Tests ---

# I will add the tests for the calculator classes and the main orchestrator function here
# after you approve this step.