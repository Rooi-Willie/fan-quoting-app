import pytest
import json
import glob
from pathlib import Path
from sqlalchemy.orm import Session
from app import crud, schemas
from app.logic.calculation_engine import calculate_single_component_details

# Get the directory of the current test file
TEST_DIR = Path(__file__).parent

# Find all JSON files in the test_data directory
json_files = glob.glob(str(TEST_DIR / "test_data/*.json"))

# Load all test cases from all JSON files
test_cases = []
for file in json_files:
    with open(file) as f:
        test_cases.extend(json.load(f))

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
