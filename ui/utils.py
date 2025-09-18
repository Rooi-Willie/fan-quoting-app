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
	"""Fetch current rates and settings from the API for context population."""
	try:
		response = requests.get(f"{API_BASE_URL}/settings/global")
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
	1. Detect input changes and POST to /components/v3-summary.
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
	for name in selected_components:
		comp_id = name_to_id.get(name)
		ov = overrides.get(name, {})
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
		_calc.setdefault("server_summary", st.session_state.get("server_summary", {}))
		_calc.setdefault("derived_totals", _recompute_derived_totals_from_server(qd))
		_calc.setdefault("rates_and_settings_used", _build_rates_snapshot(payload))
		
		# Populate context data for v3 schema
		populate_context_rates_and_settings(qd)
		
		return

	logger.debug("[DEBUG] Making API call with payload:", payload)
	try:
		# Use v3 endpoint
		resp = requests.post(f"{API_BASE_URL}/components/v3-summary", json=payload)
		resp.raise_for_status()
		server_summary = resp.json() or {}
		st.session_state.server_summary = server_summary
		st.session_state.last_summary_payload_hash = payload_hash
		# Persist into nested quote_data.calculations (v3 schema)
		_calc = qd.setdefault("calculations", {})
		_calc["server_summary"] = server_summary
		_calc["derived_totals"] = _recompute_derived_totals_from_server(qd)
		_calc["rates_and_settings_used"] = _build_rates_snapshot(payload)
		
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