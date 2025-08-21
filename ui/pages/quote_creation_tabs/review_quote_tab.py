import streamlit as st
import pandas as pd
import os
import json
import requests
from config import CURRENCY_SYMBOL

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

def render_main_content():
    st.header("5. Review & Finalize Quote")
    qd = st.session_state.quote_data
    cd = qd.get("component_details", {})

    # Project Information
    st.subheader("Project Information")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Project Name:** {qd.get('project_name', 'N/A')}")
        st.markdown(f"**Client Name:** {qd.get('client_name', 'N/A')}")
        st.markdown(f"**Quote Reference:** {qd.get('quote_ref', 'N/A')}")
    with col2:
        st.markdown(f"**Fan ID:** {qd.get('fan_uid', 'N/A')} mm")
        
    # Motor Information (more detailed)
    st.subheader("Motor Information")
    if qd.get('selected_motor_details') and isinstance(qd['selected_motor_details'], dict):
        motor = qd['selected_motor_details']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Supplier:** {motor.get('supplier_name', 'N/A')}")
            st.markdown(f"**Product Range:** {motor.get('product_range', 'N/A')}")
            st.markdown(f"**Part Number:** {motor.get('part_number', 'N/A')}")
        with col2:
            st.markdown(f"**Power:** {motor.get('rated_output', 0)} {motor.get('rated_output_unit', 'kW')}")
            st.markdown(f"**Poles:** {motor.get('poles', 'N/A')}")
            st.markdown(f"**Speed:** {motor.get('speed', 'N/A')} {motor.get('speed_unit', 'RPM')}")
        with col3:
            st.markdown(f"**Mount Type:** {qd.get('motor_mount_type', 'N/A')}")
            st.markdown(f"**Base Price:** {CURRENCY_SYMBOL} {float(qd.get('motor_price', 0)):,.2f}")
            
            # Show markup details
            motor_markup = float(qd.get('motor_markup_override', 1.0))
            motor_markup_pct = (motor_markup - 1) * 100
            st.markdown(f"**Markup Applied:** {motor_markup:.2f} ({motor_markup_pct:.1f}%)")
            
            # Final price
            if 'motor_price_after_markup' in qd:
                st.markdown(f"**Final Price:** {CURRENCY_SYMBOL} {float(qd.get('motor_price_after_markup', 0)):,.2f}")
    else:
        st.info("No motor has been selected. Please go to the 'Motor Selection' tab to choose a motor.")

    st.divider()

    # Auto-refresh authoritative server totals when inputs change
    def _ensure_server_summary_up_to_date():
        qd_local = st.session_state.get("quote_data", {}) or {}
        cd_local = qd_local.get("component_details", {}) or {}
        fan_config_id = qd_local.get("fan_config_id") or qd_local.get("fan_id")
        selected_names = qd_local.get("selected_components_unordered", []) or []
        if not fan_config_id or not selected_names:
            return

        try:
            resp = requests.get(f"{API_BASE_URL}/fans/{fan_config_id}/components")
            resp.raise_for_status()
            comps = resp.json() or []
            available_map = {c.get('name'): c.get('id') for c in comps}
        except requests.RequestException:
            return

        comp_list = []
        for name in selected_names:
            comp_id = available_map.get(name)
            overrides = cd_local.get(name, {}) if isinstance(cd_local, dict) else {}
            comp_list.append({
                "component_id": comp_id,
                "thickness_mm_override": overrides.get("Material Thickness"),
                "fabrication_waste_factor_override": (overrides.get("Fabrication Waste") / 100.0) if overrides.get("Fabrication Waste") is not None else None
            })

        payload = {
            "fan_configuration_id": fan_config_id,
            "blade_quantity": int(qd_local.get("blade_sets", 0)) if qd_local.get("blade_sets") else None,
            "components": comp_list,
            "markup_override": qd_local.get("markup_override"),
            "motor_markup_override": qd_local.get("motor_markup_override")
        }

        payload_hash = json.dumps(payload, sort_keys=True, default=str)
        if st.session_state.get("last_summary_payload_hash") == payload_hash:
            return
        try:
            resp = requests.post(f"{API_BASE_URL}/quotes/components/summary", json=payload)
            resp.raise_for_status()
            st.session_state.server_summary = resp.json()
            st.session_state.last_summary_payload_hash = payload_hash
        except requests.RequestException:
            pass

    _ensure_server_summary_up_to_date()

    # Fan Component Cost & Mass Summary (DataFrame only)
    st.subheader("Fan Component Cost & Mass Summary")

    server_components = (st.session_state.get("server_summary") or {}).get("components")
    component_calcs = st.session_state.get("component_calculations", {}) or {}

    rows = []
    if server_components:
        for c in server_components:
            rows.append({
                "Component": c.get("name"),
                "Length (mm)": c.get("total_length_mm"),
                "Real Mass (kg)": c.get("real_mass_kg"),
                "Material Cost": c.get("material_cost"),
                "Labour Cost": c.get("labour_cost"),
                "Cost Before Markup": c.get("total_cost_before_markup"),
                "Cost After Markup": c.get("total_cost_after_markup"),
            })
    else:
        for name, c in component_calcs.items():
            rows.append({
                "Component": name,
                "Length (mm)": c.get("total_length_mm"),
                "Real Mass (kg)": c.get("real_mass_kg"),
                "Material Cost": c.get("material_cost"),
                "Labour Cost": c.get("labour_cost"),
                "Cost Before Markup": c.get("total_cost_before_markup"),
                "Cost After Markup": c.get("total_cost_after_markup"),
            })

    if not rows:
        st.info("No fan components configured yet. Please go to the 'Fan Configuration' tab.")
        return

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
    df = pd.concat([df, pd.DataFrame([totals_row])], ignore_index=True, sort=False).fillna("N/A")

    def _highlight_totals(row):
        return ['font-weight: bold; font-size: 20px; color: #66b1d1;' if row['Component'] == 'TOTAL' else '' for _ in row]
    def _fmt_length(x):
        return f"{int(x):,d}" if isinstance(x, (int, float)) else x
    def _fmt_float2(x):
        return f"{x:,.2f}" if isinstance(x, (int, float)) else x
    def _fmt_currency(x):
        return f"{CURRENCY_SYMBOL} {x:,.2f}" if isinstance(x, (int, float)) else x

    styler = df.style.apply(_highlight_totals, axis=1).format({
        "Length (mm)": _fmt_length,
        "Real Mass (kg)": _fmt_float2,
        "Material Cost": _fmt_currency,
        "Labour Cost": _fmt_currency,
        "Cost Before Markup": _fmt_currency,
        "Cost After Markup": _fmt_currency,
    })
    st.write(styler)

    st.divider()
    if st.button("🖨️ Generate Quote Document (Placeholder)", use_container_width=True):
        st.success("Quote document generation logic would be triggered here!")
        st.balloons()