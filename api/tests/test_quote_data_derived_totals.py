import pytest
from app import crud


def test_extract_summary_with_nested_component_totals():
    quote_data = {
        "fan": {"uid": "fan-123", "config_id": 1},
        "components": {
            "selected": ["casing", "impeller"],
            "by_name": {
                "casing": {"calculated": {"total_cost_after_markup": 230.0}},
                "impeller": {"calculated": {"total_cost_after_markup": 138.0}},
            },
        },
        "motor": {"final_price": 900.0},
        "buy_out_items": [
            {"id": "b1", "description": "Crating", "unit_cost": 50.0, "qty": 2, "subtotal": 100.0},
            {"id": "b2", "description": "Paint", "unit_cost": 30.0, "qty": 1, "subtotal": 30.0},
        ],
        "calculation": {
            "server_summary": {"final_price": 368.0},  # components sum 230+138
            "markup_override": 1.4,
        },
    }

    summary = crud._extract_summary_from_quote_data(quote_data)

    derived = quote_data.get("calculation", {}).get("derived_totals", {})
    assert derived.get("components_final_price") == 368.0
    assert derived.get("motor_final_price") == 900.0
    assert derived.get("buyout_total") == 130.0
    assert derived.get("grand_total") == pytest.approx(1398.0)
    assert summary["fan_uid"] == "fan-123"
    assert summary["component_list"] == ["casing", "impeller"]
    assert summary["total_price"] == pytest.approx(1398.0)


def test_extract_summary_handles_missing_nodes():
    quote_data = {"calculation": {}}
    summary = crud._extract_summary_from_quote_data(quote_data)
    derived = quote_data.get("calculation", {}).get("derived_totals", {})
    assert derived.get("grand_total") == 0.0
    assert summary["component_list"] == []


def test_extract_summary_nested_only_consistency():
    quote_data = {
        "fan": {"uid": "fanX", "config_size_mm": 1200, "blade_sets": "6"},
        "components": {"selected": ["casing"], "by_name": {"casing": {"calculated": {"total_cost_after_markup": 230}}}},
        "motor": {"final_price": 500.0, "selection": {"supplier_name": "ACME", "rated_output": 55}},
        "buy_out_items": [{"id": "b", "subtotal": 20}],
        "calculation": {"server_summary": {"final_price": 230}},
    }
    summary = crud._extract_summary_from_quote_data(quote_data)
    derived = quote_data["calculation"]["derived_totals"]
    assert summary["fan_uid"] == "fanX"
    assert summary["component_list"] == ["casing"]
    assert derived["components_final_price"] == 230
    assert derived["motor_final_price"] == 500.0
    assert derived["buyout_total"] == 20
    assert derived["grand_total"] == 750.0


def test_preserve_rates_and_settings_used():
    quote_data = {
        "calculation": {
            "rates_and_settings_used": {"fan_configuration_id": 5, "markup_override": 1.4},
            "server_summary": {"final_price": 100.0},
        },
        "motor": {"final_price": 50.0},
        "buy_out_items": [],
    }
    # Call extraction (should not delete existing snapshot)
    from app import crud
    crud._extract_summary_from_quote_data(quote_data)
    calc = quote_data.get("calculation", {})
    assert calc.get("rates_and_settings_used", {}).get("fan_configuration_id") == 5
