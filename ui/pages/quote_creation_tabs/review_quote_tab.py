import streamlit as st
import pandas as pd
import os
from config import CURRENCY_SYMBOL
from utils import ensure_server_summary_up_to_date, build_summary_dataframe

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
    st.divider()
   
    # Motor Information (more detailed)
    st.subheader("Motor Information")
    if qd.get('selected_motor_details') and isinstance(qd['selected_motor_details'], dict):
        motor = qd['selected_motor_details']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Supplier:** {motor.get('supplier_name', 'N/A')}")
            st.markdown(f"**Product Range:** {motor.get('product_range', 'N/A')}")
            st.markdown(f"**Mount Type:** {qd.get('motor_mount_type', 'N/A')}")
        with col2:
            st.markdown(f"**Power:** {motor.get('rated_output', 0)} {motor.get('rated_output_unit', 'kW')}")
            st.markdown(f"**Poles:** {motor.get('poles', 'N/A')}")
            st.markdown(f"**Speed:** {motor.get('speed', 'N/A')} {motor.get('speed_unit', 'RPM')}")
        with col3:
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
    ensure_server_summary_up_to_date(qd)

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

    styler = build_summary_dataframe(rows, CURRENCY_SYMBOL)
    st.write(styler)

    st.divider()
    if st.button("🖨️ Generate Quote Document (Placeholder)", use_container_width=True):
        st.success("Quote document generation logic would be triggered here!")
        st.balloons()