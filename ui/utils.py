import os
import json
from typing import Dict, List, Optional
import datetime

import pandas as pd
from pandas.io.formats.style import Styler
import requests
import streamlit as st
import logging

# South Africa timezone (UTC+2 / SAST)
SAST_TZ = datetime.timezone(datetime.timedelta(hours=2))

def get_sast_now():
    """Return current datetime in South Africa timezone (UTC+2 / SAST)"""
    return datetime.datetime.now(SAST_TZ)

# Configure basic logging (optional, but good for setup)
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')

# Create a logger object
logger = logging.getLogger(__name__)

# Shared API base URL and API Key
try:
    API_BASE_URL = st.secrets["API_BASE_URL"] if "API_BASE_URL" in st.secrets else os.getenv("API_BASE_URL", "http://api:8080")
except (KeyError, AttributeError):
    API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8080")

try:
    API_KEY = st.secrets["API_KEY"] if "API_KEY" in st.secrets else os.getenv("API_KEY", "")
except (KeyError, AttributeError):
    API_KEY = os.getenv("API_KEY", "")

# Log what was loaded (for debugging)
logger.info(f"API_BASE_URL: {API_BASE_URL}")
logger.info(f"API_KEY loaded: {bool(API_KEY)} (length: {len(API_KEY)})")


def get_api_headers():
    """Get headers for API requests including authentication"""
    headers = {
        "Content-Type": "application/json"
    }
    
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    return headers


def api_get(endpoint: str, **kwargs):
    """Make GET request to API with authentication"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = get_api_headers()
    
    try:
        response = requests.get(url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API GET request failed: {e}")
        st.error(f"Failed to connect to API: {e}")
        return None


def api_post(endpoint: str, data: dict, **kwargs):
    """Make POST request to API with authentication"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = get_api_headers()
    
    try:
        response = requests.post(url, json=data, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API POST request failed: {e}")
        st.error(f"Failed to connect to API: {e}")
        return None


def api_patch(endpoint: str, data: dict, **kwargs):
    """Make PATCH request to API with authentication"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = get_api_headers()

    try:
        response = requests.patch(url, json=data, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API PATCH request failed: {e}")
        st.error(f"Failed to connect to API: {e}")
        return None


def api_delete(endpoint: str, data: dict = None, **kwargs):
    """Make DELETE request to API with authentication.

    Args:
        endpoint: API endpoint path (e.g. '/saved-quotes/123').
        data: Optional JSON body to send with the request.

    Returns:
        Parsed JSON response, or None on failure.
    """
    url = f"{API_BASE_URL}{endpoint}"
    headers = get_api_headers()

    try:
        response = requests.delete(url, json=data, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API DELETE request failed: {e}")
        st.error(f"Failed to connect to API: {e}")
        return None


def _recompute_derived_totals_from_server(cfg: dict) -> dict:
	"""Compute client-side derived_totals for a single fan configuration.

	Args:
		cfg: A single fan configuration dict from fan_configurations[].

	Returns:
		dict with components_final_price, motor_final_price, buyout_total, grand_total.
	"""
	if not isinstance(cfg, dict):
		return {}
	calc = cfg.get("calculations", {}) or {}
	server_summary = calc.get("server_summary") or {}
	calculated_components = calc.get("components", {}) or {}
	spec_section = cfg.get("specification", {}) or {}
	motor_calculation = calc.get("motor", {}) or {}
	buyouts = spec_section.get("buyouts", []) or []

	comp_total = None
	if isinstance(server_summary, dict):
		comp_total = server_summary.get("final_price") or server_summary.get("total_cost_after_markup")
	if comp_total is None:
		comp_total = 0.0
		for name, calc_data in calculated_components.items():
			if not isinstance(calc_data, dict):
				continue
			val = calc_data.get("total_cost_after_markup") or calc_data.get("final_price")
			if isinstance(val, (int, float)):
				comp_total += float(val)

	motor_total = motor_calculation.get("final_price") or 0.0

	buyout_total = 0.0
	if isinstance(buyouts, list):
		for item in buyouts:
			if not isinstance(item, dict):
				continue
			subtotal = item.get("subtotal")
			if subtotal is None:
				unit_cost = item.get("unit_cost") or item.get("cost") or 0
				qty = item.get("qty") or item.get("quantity") or 0
				subtotal = float(unit_cost) * float(qty)
			buyout_total += float(subtotal or 0)

	grand_total = float(comp_total or 0) + float(motor_total or 0) + float(buyout_total)
	return {
		"components_final_price": float(comp_total or 0),
		"motor_final_price": float(motor_total or 0),
		"buyout_total": float(buyout_total),
		"grand_total": float(grand_total),
	}


def _update_single_config_totals(cfg: dict) -> None:
	"""Update calculations for a single fan configuration entry.

	Prefers backend-calculated component_totals when available and consistent,
	falls back to UI calculation otherwise. Also computes unit_total and line_total.
	"""
	if not isinstance(cfg, dict):
		return

	calc_section = cfg.setdefault("calculations", {})
	spec_section = cfg.get("specification", {})

	# Check if backend has already provided authoritative component_totals
	existing_component_totals = calc_section.get("component_totals", {})
	backend_has_totals = (
		existing_component_totals and
		existing_component_totals.get("final_price") is not None and
		existing_component_totals.get("final_price") > 0
	)

	if backend_has_totals:
		components = calc_section.get("components", {})
		ui_calculated_total = sum(
			float(comp_data.get("total_cost_after_markup", 0) or 0)
			for comp_data in components.values()
			if isinstance(comp_data, dict)
		)
		backend_total = float(existing_component_totals.get("final_price", 0))
		if abs(ui_calculated_total - backend_total) >= 0.01:
			backend_has_totals = False

	if backend_has_totals:
		component_final_price = float(existing_component_totals.get("final_price", 0))
	else:
		components = calc_section.get("components", {})
		total_length_mm = 0
		total_mass_kg = 0
		total_material_cost = 0
		total_labour_cost = 0
		subtotal_cost = 0
		component_final_price = 0

		for comp_name, comp_data in components.items():
			if not isinstance(comp_data, dict):
				continue
			total_length_mm += float(comp_data.get("total_length_mm", 0) or 0)
			total_mass_kg += float(comp_data.get("real_mass_kg", 0) or 0)
			total_material_cost += float(comp_data.get("material_cost", 0) or 0)
			total_labour_cost += float(comp_data.get("labour_cost", 0) or 0)
			subtotal_cost += float(comp_data.get("total_cost_before_markup", 0) or 0)
			component_final_price += float(comp_data.get("total_cost_after_markup", 0) or 0)

		calc_section.setdefault("component_totals", {}).update({
			"total_length_mm": round(total_length_mm, 2),
			"total_mass_kg": round(total_mass_kg, 6),
			"total_labour_cost": round(total_labour_cost, 2),
			"total_material_cost": round(total_material_cost, 2),
			"subtotal_cost": round(subtotal_cost, 2),
			"final_price": round(component_final_price, 2)
		})

	# Motor total
	motor_calc = calc_section.get("motor", {})
	motor_total = float(motor_calc.get("final_price", 0))

	# Buyout total
	buyouts = spec_section.get("buyouts", []) or []
	buyout_total = 0.0
	if isinstance(buyouts, list):
		for item in buyouts:
			if not isinstance(item, dict):
				continue
			subtotal = item.get("subtotal")
			if subtotal is None:
				unit_cost = item.get("unit_cost") or item.get("cost") or 0
				qty = item.get("qty") or item.get("quantity") or 0
				subtotal = float(unit_cost) * float(qty)
			buyout_total += float(subtotal or 0)

	# Per-config totals
	config_grand_total = component_final_price + motor_total + buyout_total

	calc_section.setdefault("totals", {}).update({
		"components": round(component_final_price, 2),
		"motor": round(motor_total, 2),
		"buyouts": round(buyout_total, 2),
		"grand_total": round(config_grand_total, 2)
	})

	# Unit total and line total (quantity-aware)
	unit_total = round(config_grand_total, 2)
	qty = cfg.get("quantity", 1)
	calc_section["unit_total"] = unit_total
	calc_section["line_total"] = round(unit_total * qty, 2)


def update_quote_totals(qd: dict) -> None:
	"""Update totals for all fan configurations and compute grand totals.

	For each fan config:
	  1. Compute component/motor/buyout totals
	  2. Set unit_total and line_total (unit_total * quantity)

	Then aggregate across all configs into qd["grand_totals"].
	"""
	if not isinstance(qd, dict):
		return

	configs = qd.get("fan_configurations", [])
	if not configs:
		return

	grand_components = 0.0
	grand_motors = 0.0
	grand_buyouts = 0.0

	for cfg in configs:
		_update_single_config_totals(cfg)
		qty = cfg.get("quantity", 1)
		calcs = cfg.get("calculations", {})
		totals = calcs.get("totals", {})

		grand_components += float(totals.get("components", 0)) * qty
		grand_motors += float(totals.get("motor", 0)) * qty
		grand_buyouts += float(totals.get("buyouts", 0)) * qty

	qd["grand_totals"] = {
		"components": round(grand_components, 2),
		"motors": round(grand_motors, 2),
		"buyouts": round(grand_buyouts, 2),
		"grand_total": round(grand_components + grand_motors + grand_buyouts, 2),
	}

	logger.info(f"Quote grand totals updated. Components: {grand_components}, Motors: {grand_motors}, Buyouts: {grand_buyouts}, Grand Total: {grand_components + grand_motors + grand_buyouts}")


def _build_rates_snapshot(summary_payload: dict) -> dict:
	"""Capture pricing input snapshot for audit: overrides & key driving factors.

	The server may apply its own logic with global settings; this captures what
	the client sent (fan config id, blade qty, component ids, markup overrides).
	"""
	if not isinstance(summary_payload, dict):
		return {}
	return {
		"fan_configuration_id": summary_payload.get("fan_configuration_id"),
		"blade_quantity": summary_payload.get("blade_quantity"),
		"markup_override": summary_payload.get("markup_override"),
		"motor_markup_override": summary_payload.get("motor_markup_override"),
		"components": [
			{
				"component_id": c.get("component_id"),
				"thickness_mm_override": c.get("thickness_mm_override"),
				"fabrication_waste_factor_override": c.get("fabrication_waste_factor_override"),
			}
			for c in summary_payload.get("components", []) if isinstance(c, dict)
		],
	}


def fetch_rates_and_settings() -> dict:
	"""Fetch current rates and settings from the API for context population.
	
	Uses the /settings/rates-and-settings endpoint which includes:
	- Global settings (markup defaults, etc.)
	- Material costs and rates  
	- Labor rates
	- All consolidated settings for calculations
	"""
	try:
		response = requests.get(f"{API_BASE_URL}/settings/rates-and-settings", headers=get_api_headers())
		response.raise_for_status()
		return response.json()
	except requests.RequestException:
		return {}


def populate_context_rates_and_settings(qd: dict) -> None:
	"""Populate context.rates_and_settings with current API rates and settings."""
	if not isinstance(qd, dict):
		return
	
	context_section = qd.setdefault("context", {})
	rates_and_settings = fetch_rates_and_settings()
	
	if rates_and_settings:
		context_section['rates_and_settings'] = {
			'timestamp': get_sast_now().isoformat(),
			'full_settings_data': rates_and_settings  # Complete settings record for reference
		}


def fetch_components_map(fan_config_id: int) -> Dict[str, int]:
	"""Return a {name: id} map for components of a fan config, or {} on error."""
	if not fan_config_id:
		return {}
	try:
		resp = requests.get(f"{API_BASE_URL}/fans/{fan_config_id}/components", headers=get_api_headers())
		resp.raise_for_status()
		comps = resp.json() or []
		return {c.get('name'): c.get('id') for c in comps}
	except requests.RequestException:
		return {}


def ensure_server_summary_up_to_date(qd: dict) -> None:
	"""Update server-side component summary for the active fan configuration.

	Operates on the active fan config within the v4 fan_configurations[] array.
	Calls the existing /quotes/components/v3-summary endpoint per-config.
	"""
	logger.debug("ensure_server_summary_up_to_date called")
	if not isinstance(qd, dict):
		return

	from common import get_active_config
	active_cfg = get_active_config(qd)
	if not active_cfg:
		return

	spec_section = active_cfg.get("specification", {})
	fan_section = spec_section.get("fan", {})
	fan_config = fan_section.get("fan_configuration", {})
	selected_components = spec_section.get("components", [])
	pricing_section = active_cfg.get("pricing", {})

	fan_config_id = fan_config.get("id")
	if not fan_config_id or not selected_components:
		return

	name_to_id = fetch_components_map(int(fan_config_id))

	overrides = pricing_section.get("overrides", {}) or {}
	comp_list = []

	for comp_item in selected_components:
		comp_id = comp_item.get("id")
		comp_name = comp_item.get("name")

		if comp_id and comp_name:
			ov = overrides.get(comp_name, {})
			comp_list.append({
				"component_id": comp_id,
				"thickness_mm_override": ov.get("material_thickness_mm"),
				"fabrication_waste_factor_override": (ov.get("fabrication_waste_pct") / 100.0) if ov.get("fabrication_waste_pct") is not None else None
			})

	payload = {
		"fan_configuration_id": int(fan_config_id),
		"blade_quantity": int(fan_section.get("blade_sets") or 0),
		"components": comp_list,
		"markup_override": pricing_section.get("component_markup"),
		"motor_markup_override": pricing_section.get("motor_markup")
	}

	payload_hash = json.dumps(payload, sort_keys=True, default=str)

	if st.session_state.get("last_summary_payload_hash") == payload_hash:
		# Ensure persisted structures exist even if no call needed
		_calc = active_cfg.setdefault("calculations", {})

		cached_response = st.session_state.get("server_summary", {})
		calculations_from_cache = cached_response.get("calculations", {})

		if calculations_from_cache:
			if "components" in calculations_from_cache:
				_calc["components"] = calculations_from_cache["components"]
			if "component_totals" in calculations_from_cache:
				_calc["component_totals"] = calculations_from_cache["component_totals"]
			if "totals" in calculations_from_cache:
				_calc["totals"] = calculations_from_cache["totals"]
			if "motor" in calculations_from_cache:
				_calc["motor"] = calculations_from_cache["motor"]

		_calc.setdefault("server_summary", cached_response)
		_calc.setdefault("derived_totals", _recompute_derived_totals_from_server(active_cfg))
		_calc.setdefault("rates_and_settings_used", _build_rates_snapshot(payload))

		update_quote_totals(qd)
		populate_context_rates_and_settings(qd)
		return

	try:
		resp = requests.post(f"{API_BASE_URL}/quotes/components/v3-summary", json=payload, headers=get_api_headers())
		resp.raise_for_status()
		api_response = resp.json() or {}

		calculations_from_api = api_response.get("calculations", {})

		st.session_state.server_summary = api_response
		st.session_state.last_summary_payload_hash = payload_hash

		_calc = active_cfg.setdefault("calculations", {})

		if calculations_from_api:
			if "components" in calculations_from_api:
				_calc["components"] = calculations_from_api["components"]
			if "component_totals" in calculations_from_api:
				_calc["component_totals"] = calculations_from_api["component_totals"]
			if "totals" in calculations_from_api:
				_calc["totals"] = calculations_from_api["totals"]
			if "motor" in calculations_from_api:
				_calc["motor"] = calculations_from_api["motor"]

		_calc["server_summary"] = api_response
		_calc["derived_totals"] = _recompute_derived_totals_from_server(active_cfg)
		_calc["rates_and_settings_used"] = _build_rates_snapshot(payload)

		update_quote_totals(qd)
		populate_context_rates_and_settings(qd)
	except requests.RequestException:
		pass

def build_summary_dataframe(rows: List[Dict], currency_symbol: str) -> Styler:
	"""Return a styled DataFrame with a TOTAL row and nice formatting."""
	df = pd.DataFrame(rows)

	def _safe_sum(key: str) -> float:
		vals = pd.to_numeric(df[key], errors='coerce') if key in df.columns else pd.Series(dtype=float)
		return float(vals.fillna(0).sum())

	totals_row = {
		"Component": "TOTAL",
		"Length (mm)": _safe_sum("Length (mm)"),
		"Real Mass (kg)": _safe_sum("Real Mass (kg)"),
		"Material Cost": _safe_sum("Material Cost"),
		"Labour Cost": _safe_sum("Labour Cost"),
		"Cost Before Markup": _safe_sum("Cost Before Markup"),
		"Cost After Markup": _safe_sum("Cost After Markup"),
	}
	df = pd.concat([df, pd.DataFrame([totals_row])], ignore_index=True, sort=False).fillna(0)

	def _highlight_totals(row):
		return ['font-weight: bold; font-size: 20px; color: #66b1d1;' if row['Component'] == 'TOTAL' else '' for _ in row]
	def _fmt_length(x):
		return f"{int(x):,d}" if isinstance(x, (int, float)) else x
	def _fmt_float2(x):
		return f"{x:,.2f}" if isinstance(x, (int, float)) else x
	def _fmt_currency(x):
		return f"{currency_symbol} {x:,.2f}" if isinstance(x, (int, float)) else x

	styler = df.style.apply(_highlight_totals, axis=1).format({
		"Length (mm)": _fmt_length,
		"Real Mass (kg)": _fmt_float2,
		"Material Cost": _fmt_currency,
		"Labour Cost": _fmt_currency,
		"Cost Before Markup": _fmt_currency,
		"Cost After Markup": _fmt_currency,
	})
	return styler


def get_ordered_component_names(quote_data_or_config: dict, fan_config_entry: dict = None) -> List[str]:
	"""Get component names ordered by the database order_by column.

	Can be called with either a full quote_data dict (uses active config)
	or with a specific fan_config_entry dict.

	Args:
		quote_data_or_config: Either full quote_data or a single fan config entry.
		fan_config_entry: If provided, use this config entry instead of active config.

	Returns:
		List of component names in DB order.
	"""
	from common import get_available_components, get_active_config

	cfg = fan_config_entry
	if cfg is None:
		# Try to use as quote_data with active config
		if "fan_configurations" in quote_data_or_config:
			cfg = get_active_config(quote_data_or_config)
		else:
			# Assume it's a config entry itself
			cfg = quote_data_or_config

	if not cfg:
		return []

	spec_section = cfg.get("specification", {})
	fan_section = spec_section.get("fan", {})
	fan_config_data = fan_section.get("fan_configuration", {})
	fan_config_id = fan_config_data.get("id")

	if not fan_config_id:
		return []

	available_components = get_available_components(fan_config_id)
	if not available_components:
		return []

	return [comp['name'] for comp in available_components]


def build_ordered_component_rows(component_calcs: Dict, ordered_names: List[str]) -> List[Dict]:
	"""
	Build component rows for summary table in the correct DB order.
	
	This function ensures that component rows appear in the same order as defined
	in the database components.order_by column, rather than dict insertion order.
	
	Args:
		component_calcs: Dict mapping component name to calculation results
		ordered_names: List of component names in desired display order (from get_ordered_component_names)
		
	Returns:
		List of row dicts ordered correctly for DataFrame display
	"""
	rows = []
	for comp_name in ordered_names:
		if comp_name in component_calcs:
			c = component_calcs[comp_name]
			rows.append({
				"Component": c.get("name", comp_name),
				"Length (mm)": c.get("total_length_mm"),
				"Real Mass (kg)": c.get("real_mass_kg"),
				"Material Cost": c.get("material_cost"),
				"Labour Cost": c.get("labour_cost"),
				"Cost Before Markup": c.get("total_cost_before_markup"),
				"Cost After Markup": c.get("total_cost_after_markup"),
			})
	return rows