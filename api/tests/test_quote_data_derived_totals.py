import pytest
from app import crud


def test_extract_summary_with_schema():
    """Test schema summary extraction with component and motor pricing."""
    quote_data = {
        "meta": {"version": 3, "created_at": "2025-01-01T00:00:00Z"},
        "quote": {"id": "test-quote-123"},
        "specification": {
            "fan": {
                "blade_sets": "12",
                "fan_configuration": {"uid": "fan-123", "fan_size_mm": 1200}
            },
            "motor": {
                "mount_type": "Flange",
                "motor_details": {"supplier_name": "ACME", "rated_output": 55}
            },
            "components": [
                {"name": "casing", "material_thickness_mm": 6},
                {"name": "impeller", "material_thickness_mm": 4}
            ],
            "buyouts": [
                {"id": "b1", "description": "Crating", "unit_cost": 50.0, "qty": 2, "subtotal": 100.0},
                {"id": "b2", "description": "Paint", "unit_cost": 30.0, "qty": 1, "subtotal": 30.0}
            ]
        },
        "pricing": {
            "component_markup": 1.4,
            "motor_markup": 1.2,
            "buy_out_items": []
        },
        "calculations": {
            "component_totals": {"final_price": 368.0},
            "motor": {"final_price": 900.0}
        }
    }

    summary = crud._extract_summary_from_quote_data(quote_data)

    assert summary["fan_uid"] == "fan-123"
    assert summary["fan_size_mm"] == 1200
    assert summary["blade_sets"] == 12
    assert summary["component_list"] == ["casing", "impeller"]
    assert summary["component_markup"] == 1.4
    assert summary["motor_markup"] == 1.2
    assert summary["motor_supplier"] == "ACME"
    assert summary["motor_rated_output"] == "55"
    assert summary["total_price"] == pytest.approx(1398.0)  # 368 + 900 + 130


def test_extract_summary_handles_missing_nodes():
    """Test schema with missing optional nodes."""
    quote_data = {
        "meta": {"version": 3},
        "quote": {},
        "specification": {},
        "pricing": {},
        "calculations": {}
    }
    
    summary = crud._extract_summary_from_quote_data(quote_data)
    
    assert summary["fan_uid"] is None
    assert summary["component_list"] == []
    assert summary["total_price"] == 0.0


def test_extract_summary_buyout_calculation():
    """Test schema buyout total calculation."""
    quote_data = {
        "meta": {"version": 3},
        "specification": {
            "fan": {
                "blade_sets": "6",
                "fan_configuration": {"uid": "fanX", "fan_size_mm": 1200}
            },
            "motor": {
                "mount_type": "Flange",
                "motor_details": {"supplier_name": "ACME", "rated_output": 55}
            },
            "components": [{"name": "casing"}]
        },
        "pricing": {
            "motor_markup": 1.2,
            "buy_out_items": [{"id": "b", "subtotal": 20}]
        },
        "calculations": {
            "component_totals": {"final_price": 230},
            "motor": {"final_price": 500.0}
        }
    }
    
    summary = crud._extract_summary_from_quote_data(quote_data)
    
    assert summary["fan_uid"] == "fanX"
    assert summary["component_list"] == ["casing"]
    assert summary["total_price"] == 750.0  # 230 + 500 + 20

