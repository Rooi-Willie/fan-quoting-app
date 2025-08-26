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
	"""
	Build a summary payload from session state and POST to /quotes/components/summary
	only when inputs change. Stores response in st.session_state.server_summary.
	"""
	logger.debug("ensure_server_summary_up_to_date called")
	if not isinstance(qd, dict):
		return
	cd = qd.get("component_details", {}) or {}
	fan_config_id = qd.get("fan_config_id") or qd.get("fan_id")
	selected_names = qd.get("selected_components_unordered", []) or []
	if not fan_config_id or not selected_names:
		return

	name_to_id = fetch_components_map(int(fan_config_id))

	comp_list = []
	for name in selected_names:
		comp_id = name_to_id.get(name)
		overrides = cd.get(name, {}) if isinstance(cd, dict) else {}
		comp_list.append({
			"component_id": comp_id,
			"thickness_mm_override": overrides.get("Material Thickness"),
			"fabrication_waste_factor_override": (overrides.get("Fabrication Waste") / 100.0) if overrides.get("Fabrication Waste") is not None else None
		})

	payload = {
		"fan_configuration_id": int(fan_config_id),
		"blade_quantity": int(qd.get("blade_sets", 0)) if qd.get("blade_sets") else None,
		"components": comp_list,
		"markup_override": qd.get("markup_override"),
		"motor_markup_override": qd.get("motor_markup_override")
	}

	payload_hash = json.dumps(payload, sort_keys=True, default=str)
	logger.debug(f"[DEBUG] New hash: {payload_hash[:30]}...")
	logger.debug(f"[DEBUG] Old hash: {st.session_state.get('last_summary_payload_hash', 'None')[:30]}...")

	if st.session_state.get("last_summary_payload_hash") == payload_hash:
		logger.debug("[DEBUG] Skipping API call - payload unchanged")
		return

	logger.debug("[DEBUG] Making API call with payload:", payload)
	try:
		resp = requests.post(f"{API_BASE_URL}/quotes/components/summary", json=payload)
		resp.raise_for_status()
		st.session_state.server_summary = resp.json()
		st.session_state.last_summary_payload_hash = payload_hash
		# Add explicit rerun when the server summary changes
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