import os
import json
from typing import Dict, List, Optional

import pandas as pd
from pandas.io.formats.style import Styler
import requests
import streamlit as st
import logging

# Configure basic logging (optional, but good for quick setup)
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')

# Create a logger object
logger = logging.getLogger(__name__)

# Shared API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")


def _recompute_derived_totals_from_server(qd: dict) -> dict:
	"""Compute client-side derived_totals using current quote_data and server_summary (v3 schema).

	Priority order:
	  1. calculations.server_summary.final_price (components aggregate)
	  2. sum of calculations.components[*].total_cost_after_markup (if nested present)
	Motor from v3 calculations.motor section, buy-outs from v3 specification.buyouts.
	"""
	if not isinstance(qd, dict):
		return {}
	calc = qd.get("calculations", {}) or {}
	server_summary = calc.get("server_summary") or {}
	calculated_components = calc.get("components", {}) or {}
	pricing_section = qd.get("pricing", {}) or {}
	spec_section = qd.get("specification", {}) or {}
	motor_calculation = calc.get("motor", {}) or {}  # Motor pricing moved to calculations
	buyouts = spec_section.get("buyouts", []) or []

	comp_total = None
	if isinstance(server_summary, dict):
		comp_total = server_summary.get("final_price") or server_summary.get("total_cost_after_markup")
	if comp_total is None:
		# Fallback: sum calculated component values from v3 calculations
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


def update_quote_totals(qd: dict) -> None:
	"""Update the calculations.totals and component_totals sections based on current components, motor, and buyouts.
	
	This function prefers backend-calculated component_totals when available (backend is authoritative),
	and only falls back to client-side calculation when backend data is missing or incomplete.
	UI is responsible for adding motor and buyout totals to the backend component totals.
	
	Performs consistency checking: if backend component_totals don't match the sum of individual 
	components (indicating UI changes after backend caching), falls back to UI calculation.
	
	Logs which calculation method (BACKEND or UI FALLBACK) is used for transparency and debugging.
	"""
	if not isinstance(qd, dict):
		return
		
	calc_section = qd.get("calculations", {})
	spec_section = qd.get("specification", {})
	
	# Check if backend has already provided authoritative component_totals
	existing_component_totals = calc_section.get("component_totals", {})
	backend_has_totals = (
		existing_component_totals and 
		existing_component_totals.get("final_price") is not None and
		existing_component_totals.get("final_price") > 0
	)
	
	# If backend has totals, verify they're consistent with individual components
	# If not consistent, fallback to UI calculation (individual components may have been updated)
	if backend_has_totals:
		components = calc_section.get("components", {})
		ui_calculated_total = sum(
			float(comp_data.get("total_cost_after_markup", 0) or 0)
			for comp_data in components.values()
			if isinstance(comp_data, dict)
		)
		backend_total = float(existing_component_totals.get("final_price", 0))
		
		# Allow for small rounding differences (within 0.01)
		totals_are_consistent = abs(ui_calculated_total - backend_total) < 0.01
		
		if not totals_are_consistent:
			logger.info(f"Backend component totals ({backend_total}) inconsistent with individual components ({ui_calculated_total}). Using UI calculation.")
			backend_has_totals = False
		else:
			logger.debug(f"Backend component totals ({backend_total}) consistent with individual components ({ui_calculated_total}).")
	
	if backend_has_totals:
		# Backend is authoritative - use its component calculations
		component_final_price = float(existing_component_totals.get("final_price", 0))
		logger.info(f"Using BACKEND calculations for component totals. Component final price: {component_final_price}")
	else:
		# Fallback: Calculate component totals from individual component calculations
		components = calc_section.get("components", {})
		logger.info(f"Using UI FALLBACK calculations for component totals. Found {len(components)} individual components to aggregate.")
		
		total_length_mm = 0
		total_mass_kg = 0
		total_material_cost = 0
		total_labour_cost = 0
		subtotal_cost = 0
		component_final_price = 0
		
		for comp_name, comp_data in components.items():
			if not isinstance(comp_data, dict):
				continue
				
			# Sum up the individual component values
			total_length_mm += float(comp_data.get("total_length_mm", 0) or 0)
			total_mass_kg += float(comp_data.get("real_mass_kg", 0) or 0)
			total_material_cost += float(comp_data.get("material_cost", 0) or 0)
			total_labour_cost += float(comp_data.get("labour_cost", 0) or 0)
			subtotal_cost += float(comp_data.get("total_cost_before_markup", 0) or 0)
			component_final_price += float(comp_data.get("total_cost_after_markup", 0) or 0)
		
		logger.info(f"UI calculated component totals - Final price: {component_final_price}, Material: {total_material_cost}, Labour: {total_labour_cost}")
		
		# Update component_totals section only if backend didn't provide it
		calc_section.setdefault("component_totals", {}).update({
			"total_length_mm": round(total_length_mm, 2),
			"total_mass_kg": round(total_mass_kg, 6),
			"total_labour_cost": round(total_labour_cost, 2),
			"total_material_cost": round(total_material_cost, 2),
			"subtotal_cost": round(subtotal_cost, 2),
			"final_price": round(component_final_price, 2)
		})
	
	# Get motor total from motor calculation
	motor_calc = calc_section.get("motor", {})
	motor_total = float(motor_calc.get("final_price", 0))
	
	# Calculate buyout total from specification buyouts
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
	
	# Calculate grand total using the calculated component total (backend or client-side)
	grand_total = component_final_price + motor_total + buyout_total
	
	# Update totals section
	calc_section.setdefault("totals", {}).update({
		"components": round(component_final_price, 2),
		"motor": round(motor_total, 2),
		"buyouts": round(buyout_total, 2),
		"grand_total": round(grand_total, 2)
	})
	
	# Log final calculation summary
	calculation_method = "BACKEND" if backend_has_totals else "UI FALLBACK"
	logger.info(f"Quote totals updated using {calculation_method} method. Components: {component_final_price}, Motor: {motor_total}, Buyouts: {buyout_total}, Grand Total: {grand_total}")


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
		response = requests.get(f"{API_BASE_URL}/settings/rates-and-settings")
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
			'timestamp': pd.Timestamp.now().isoformat(),
			'full_settings_data': rates_and_settings  # Complete settings record for reference
		}


def fetch_components_map(fan_config_id: int) -> Dict[str, int]:
	"""Return a {name: id} map for components of a fan config, or {} on error."""
	if not fan_config_id:
		return {}
	try:
		resp = requests.get(f"{API_BASE_URL}/fans/{fan_config_id}/components")
		resp.raise_for_status()
		comps = resp.json() or []
		return {c.get('name'): c.get('id') for c in comps}
	except requests.RequestException:
		return {}


def ensure_server_summary_up_to_date(qd: dict) -> None:
	"""Update server-side component summary using v3 schema and persist aggregates in quote_data.

	Responsibilities (v3 Schema):
	1. Detect input changes and POST to /quotes/components/v3-summary.
	2. Store raw server response in st.session_state.server_summary.
	3. Persist a snapshot under qd["calculations"]["server_summary"].
	4. Persist/refresh qd["calculations"]["derived_totals"] (client-side convenience).
	5. Persist qd["calculations"]["rates_and_settings_used"] capturing pricing inputs.

	Notes:
	- Uses v3 schema structure with proper section organization
	- Backend will still derive authoritative totals; client copy improves transparency.
	- Idempotent: if payload unchanged, does nothing.
	"""
	logger.debug("ensure_server_summary_up_to_date called")
	if not isinstance(qd, dict):
		return
	
	# Get v3 schema sections (updated for new structure)
	spec_section = qd.get("specification", {})
	fan_section = spec_section.get("fan", {})
	fan_config = fan_section.get("fan_configuration", {})
	selected_components = spec_section.get("components", [])  # This is an array in v3
	calc_section = qd.get("calculations", {})
	pricing_section = qd.get("pricing", {})
	
	fan_config_id = fan_config.get("id")
	if not fan_config_id or not selected_components:
		return

	name_to_id = fetch_components_map(int(fan_config_id))

	# In v3, overrides are in pricing.overrides, not component.overrides
	overrides = pricing_section.get("overrides", {}) or {}
	comp_list = []
	
	# Process component objects with id and name
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
		"blade_quantity": int(fan_section.get("blade_sets", 0)) if fan_section.get("blade_sets") else None,
		"components": comp_list,
		"markup_override": pricing_section.get("component_markup"),  # v3: component markup is in pricing
		"motor_markup_override": pricing_section.get("motor_markup")  # v3: motor markup is also in pricing
	}

	payload_hash = json.dumps(payload, sort_keys=True, default=str)
	logger.debug(f"[DEBUG] New hash: {payload_hash[:30]}...")
	logger.debug(f"[DEBUG] Old hash: {st.session_state.get('last_summary_payload_hash', 'None')[:30]}...")

	if st.session_state.get("last_summary_payload_hash") == payload_hash:
		logger.debug("[DEBUG] Skipping API call - payload unchanged")
		# Ensure persisted structures exist even if no call needed
		_calc = qd.setdefault("calculations", {})
		
		# Extract calculations from cached server summary if available
		cached_response = st.session_state.get("server_summary", {})
		calculations_from_cache = cached_response.get("calculations", {})
		
		if calculations_from_cache:
			# Update calculations section with cached data
			if "components" in calculations_from_cache:
				_calc["components"] = calculations_from_cache["components"]
			if "component_totals" in calculations_from_cache:
				_calc["component_totals"] = calculations_from_cache["component_totals"]
			if "totals" in calculations_from_cache:
				_calc["totals"] = calculations_from_cache["totals"]
			if "motor" in calculations_from_cache:
				_calc["motor"] = calculations_from_cache["motor"]
		
		_calc.setdefault("server_summary", cached_response)
		_calc.setdefault("derived_totals", _recompute_derived_totals_from_server(qd))
		_calc.setdefault("rates_and_settings_used", _build_rates_snapshot(payload))
		
		# Update quote totals to ensure synchronization - this will handle consistency checking
		update_quote_totals(qd)
		
		# Populate context data for v3 schema
		populate_context_rates_and_settings(qd)
		
		return

	logger.debug("[DEBUG] Making API call with payload:", payload)
	try:
		# Use v3 endpoint (correct path with quotes prefix)
		resp = requests.post(f"{API_BASE_URL}/quotes/components/v3-summary", json=payload)
		resp.raise_for_status()
		api_response = resp.json() or {}
		
		# Extract calculations section from API response
		calculations_from_api = api_response.get("calculations", {})
		
		# Store the API response for backward compatibility  
		st.session_state.server_summary = api_response
		st.session_state.last_summary_payload_hash = payload_hash
		
		# Persist into nested quote_data.calculations (v3 schema)
		_calc = qd.setdefault("calculations", {})
		
		# Update calculations section with API response data
		if calculations_from_api:
			# Store the individual component calculations
			if "components" in calculations_from_api:
				_calc["components"] = calculations_from_api["components"]
			
			# Store the component totals
			if "component_totals" in calculations_from_api:
				_calc["component_totals"] = calculations_from_api["component_totals"]
			
			# Store the final totals (components + motor + buyouts)
			if "totals" in calculations_from_api:
				_calc["totals"] = calculations_from_api["totals"]
			
			# Store motor calculations if present
			if "motor" in calculations_from_api:
				_calc["motor"] = calculations_from_api["motor"]
		
		# Keep legacy server_summary for backward compatibility
		_calc["server_summary"] = api_response
		_calc["derived_totals"] = _recompute_derived_totals_from_server(qd)
		_calc["rates_and_settings_used"] = _build_rates_snapshot(payload)
		
		# Update quote totals to ensure synchronization
		update_quote_totals(qd)
		
		# Populate context data for v3 schema
		populate_context_rates_and_settings(qd)
		
		# Trigger rerun so UI reflects new totals
		st.rerun()
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