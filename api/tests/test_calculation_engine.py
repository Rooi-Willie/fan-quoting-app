import pytest
import json
from pathlib import Path
from sqlalchemy.orm import Session
from app import crud, schemas
from app.logic.calculation_engine import calculate_single_component_details

# Get the directory of the current test file
TEST_DIR = Path(__file__).parent

# Load the test data from the JSON file
with open(TEST_DIR / "test_data/1016_fan_component_cases.json") as f:
    test_cases = json.load(f)

@pytest.mark.parametrize("test_case", test_cases)
def test_calculate_single_component_details(db_session: Session, test_case):
    """
    Tests the calculate_single_component_details function with various fan components.
    """
    # 1. Arrange
    request_payload = test_case["request_payload"]
    expected_response = test_case["expected_response"]
    
    request = schemas.ComponentCalculationRequest(**request_payload)

    # 2. Act
    result = calculate_single_component_details(db_session, request)

    # 3. Assert
    assert result.name == expected_response["name"]
    
    for key, value in expected_response["calculated_values"].items():
        assert getattr(result, key) == pytest.approx(value, rel=1e-2)