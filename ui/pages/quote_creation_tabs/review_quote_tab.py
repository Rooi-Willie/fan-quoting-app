import streamlit as st
import pandas as pd
import os
import requests
from config import CURRENCY_SYMBOL
from utils import ensure_server_summary_up_to_date, build_summary_dataframe
from pages.common import migrate_flat_to_nested_if_needed, _new_nested_quote_data

# API_BASE_URL should be configured, e.g., via environment variable
# Fallback is provided for local development.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

def render_main_content():
    st.header("5. Review & Finalize Quote")

    # Ensure nested schema
    if "quote_data" not in st.session_state or not isinstance(st.session_state.quote_data, dict):
        st.session_state.quote_data = _new_nested_quote_data()
    else:
        st.session_state.quote_data = migrate_flat_to_nested_if_needed(st.session_state.quote_data)
    qd = st.session_state.quote_data

    project = qd.get("project", {})
    fan = qd.get("fan", {})
    motor_node = qd.get("motor", {})
    calc_node = qd.get("calculation", {})
    components_node = qd.get("components", {})
    by_name = components_node.get("by_name", {})

    # Project Information
    st.subheader("Project Information")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Project Name:** {project.get('name') or 'N/A'}")
        st.markdown(f"**Client Name:** {project.get('client') or 'N/A'}")
        st.markdown(f"**Quote Reference:** {project.get('reference') or 'N/A'}")
    with col2:
        st.markdown(f"**Location:** {project.get('location') or 'N/A'}")
        st.markdown(f"**Fan ID:** {fan.get('uid') or 'N/A'}")
    st.divider()
   
    # Motor Information
    st.subheader("Motor Information")
    if motor_node.get('selection') and isinstance(motor_node['selection'], dict):
        motor = motor_node['selection']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Supplier:** {motor.get('supplier_name', 'N/A')}")
            st.markdown(f"**Product Range:** {motor.get('product_range', 'N/A')}")
            st.markdown(f"**Mount Type:** {motor_node.get('mount_type', 'N/A')}")
        with col2:
            st.markdown(f"**Power:** {motor.get('rated_output', 0)} {motor.get('rated_output_unit', 'kW')}")
            st.markdown(f"**Poles:** {motor.get('poles', 'N/A')}")
            st.markdown(f"**Speed:** {motor.get('speed', 'N/A')} {motor.get('speed_unit', 'RPM')}")
        with col3:
            base_price = motor_node.get('base_price') or motor.get('price_total', 0)
            st.markdown(f"**Base Price:** {CURRENCY_SYMBOL} {float(base_price or 0):,.2f}")
            motor_markup = float(motor_node.get('markup_override') or 1.0)
            motor_markup_pct = (motor_markup - 1) * 100
            st.markdown(f"**Markup Applied:** {motor_markup:.2f} ({motor_markup_pct:.1f}%)")
            final_price = motor_node.get('final_price')
            if final_price is not None:
                st.markdown(f"**Final Price:** {CURRENCY_SYMBOL} {float(final_price):,.2f}")
    else:
        st.info("No motor has been selected. Please go to the 'Motor Selection' tab to choose a motor.")

    st.divider()

    # Auto-refresh authoritative server totals when inputs change
    ensure_server_summary_up_to_date(qd)

    # Fan Component Cost & Mass Summary (DataFrame only)
    st.subheader("Fan Component Cost & Mass Summary")

    server_components = (st.session_state.get("server_summary") or {}).get("components")

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
        # Fallback from nested per-component calculations if server summary absent
        for name, node in by_name.items():
            calc = (node or {}).get("calculated", {})
            rows.append({
                "Component": name,
                "Length (mm)": calc.get("total_length_mm"),
                "Real Mass (kg)": calc.get("real_mass_kg"),
                "Material Cost": calc.get("material_cost"),
                "Labour Cost": calc.get("labour_cost"),
                "Cost Before Markup": calc.get("total_cost_before_markup"),
                "Cost After Markup": calc.get("total_cost_after_markup"),
            })

    if not rows:
        st.info("No fan components configured yet. Please go to the 'Fan Configuration' tab.")
        return

    styler = build_summary_dataframe(rows, CURRENCY_SYMBOL)
    st.write(styler)

    # Final Quote Cost Breakdown Section
    st.divider()
    st.subheader("Final Quote Cost Breakdown")

    # Get data from session state
    server_summary = st.session_state.get("server_summary", {})
    
    # Initialize breakdown data
    breakdown_rows = []
    
    # Add Component section with all components
    if server_components:
        # Add each individual component
        for i, c in enumerate(server_components):
            breakdown_rows.append({
                "Item Type": "Component",
                "Item": c.get("name", f"Component {i+1}"),
                "Cost": c.get("total_cost_after_markup", 0)
            })
        
        # Add Component Subtotal
        components_total = server_summary.get("final_price", 0)
        breakdown_rows.append({
            "Item Type": "Subtotal",
            "Item": "Components Subtotal",
            "Cost": components_total
        })
    
    # Add Motor section if a motor is selected
    if motor_node.get('selection'):
        motor = motor_node['selection']
        motor_price = float(motor_node.get('final_price', 0) or 0)
        
        # Add motor entry
        motor_name = f"{motor.get('supplier_name', '')} {motor.get('product_range', '')} - {motor.get('rated_output', 0)} {motor.get('rated_output_unit', 'kW')}"
        breakdown_rows.append({
            "Item Type": "Motor",
            "Item": motor_name,
            "Cost": motor_price
        })
        
        # Add Motor Subtotal
        breakdown_rows.append({
            "Item Type": "Subtotal",
            "Item": "Motor Subtotal",
            "Cost": motor_price
        })
    
    # Add Buyout Items section placeholder
    # Buy-out items subtotal
    buyout_items = qd.get("buy_out_items", [])
    buyout_total = 0.0
    if isinstance(buyout_items, list) and buyout_items:
        for bi in buyout_items:
            buyout_total += float(bi.get("subtotal") or (bi.get("unit_cost", 0) * bi.get("qty", 0)))
        breakdown_rows.append({
            "Item Type": "Subtotal",
            "Item": "Buy-out Items Subtotal",
            "Cost": buyout_total
        })
    else:
        breakdown_rows.append({
            "Item Type": "Subtotal",
            "Item": "Buy-out Items Subtotal",
            "Cost": 0
        })
    
    # Calculate and add Final Total
    components_total = server_summary.get("final_price", 0) or 0
    motor_total = float(motor_node.get('final_price', 0) or 0)
    final_total = components_total + motor_total + buyout_total
    
    # Add Final Total Row
    breakdown_rows.append({
        "Item Type": "Total",
        "Item": "FINAL QUOTE TOTAL",
        "Cost": final_total
    })
    
    # Create DataFrame
    df = pd.DataFrame(breakdown_rows)
    
    # Format the cost column
    df["Formatted Cost"] = df["Cost"].apply(lambda x: f"{CURRENCY_SYMBOL} {float(x):,.2f}")
    
    # Keep only necessary columns for display
    display_df = df[["Item", "Formatted Cost"]]
    
    # Apply styling to the table
    def highlight_rows(row):
        style = ''
        if df.loc[row.name, "Item Type"] == "Subtotal":
            style = 'font-weight: bold; border-top: 1px solid; color: #1E88E5'
        elif df.loc[row.name, "Item Type"] == "Total":
            style = 'font-weight: bold; font-size: 1.1em; border-top: 2px solid; color: #2E7D32'
        return [style, style]  # Return styling for exactly 2 columns
    
    # Apply styling
    styled_df = display_df.style.apply(highlight_rows, axis=1)
    
    # Show the table
    st.table(styled_df)

    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        # Existing Generate PDF button
        if st.button("📄 Generate Quote Document", use_container_width=True):
            st.success("Quote document generation logic would be triggered here!")
            st.balloons()
    
    with col2:
        # New Save Quote button
        if st.button("💾 Save Quote", use_container_width=True):
            if save_quote():
                st.success("Quote saved successfully!")
                # Add option to view the quote or continue editing
                if st.button("View Saved Quotes"):
                    st.switch_page("pages/3_View_Existing_Quotes.py")

def save_quote():
    """Save the current quote to the database"""
    try:
        # Get current user ID (use 1 for development until auth is implemented)
        user_id = 1
        qd = st.session_state.quote_data
        project = qd.get("project", {}) if isinstance(qd, dict) else {}

        # Prepare payload using nested project node
        payload = {
            "quote_ref": project.get("reference") or qd.get("quote_ref"),
            "client_name": project.get("client") or qd.get("client_name"),
            "project_name": project.get("name") or qd.get("project_name"),
            "project_location": project.get("location") or qd.get("project_location"),
            "user_id": user_id,
            "quote_data": qd,
        }
        
        # Call API
        response = requests.post(f"{API_BASE_URL}/saved-quotes/", json=payload)
        response.raise_for_status()
        
        # Store the quote ID in session state for reference
        saved_quote = response.json()
        st.session_state["last_saved_quote_id"] = saved_quote["id"]
        
        return True
    except Exception as e:
        st.error(f"Error saving quote: {str(e)}")
        return False