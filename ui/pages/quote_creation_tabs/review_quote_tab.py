import streamlit as st
import pandas as pd
import os
import requests
from config import CURRENCY_SYMBOL
from utils import ensure_server_summary_up_to_date, build_summary_dataframe

# API_BASE_URL should be configured, e.g., via environment variable
# Fallback is provided for local development.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

def render_main_content():
    st.header("5. Review & Finalize Quote")
    
    # Import shared_logic here to avoid circular imports
    from pages.quote_creation_tabs import shared_logic
    
    # Initialize/ensure the nested structure exists
    shared_logic.init_quote_data_structure()
    
    qd = st.session_state.quote_data
    cd = qd.get("component_details", {})

    # Project Information
    st.subheader("Project Information")
    col1, col2 = st.columns(2)
    with col1:
        # Get project info from either new or legacy structure
        project_name = None
        client_name = None
        quote_ref = None
        
        if "project_info" in qd and isinstance(qd["project_info"], dict):
            project_name = qd["project_info"].get("name")
            client_name = qd["project_info"].get("client")
            quote_ref = qd["project_info"].get("quote_ref")
            
        if project_name is None:
            project_name = qd.get('project_name', 'N/A')
        if client_name is None:
            client_name = qd.get('client_name', 'N/A')
        if quote_ref is None:
            quote_ref = qd.get('quote_ref', 'N/A')
            
        st.markdown(f"**Project Name:** {project_name}")
        st.markdown(f"**Client Name:** {client_name}")
        st.markdown(f"**Quote Reference:** {quote_ref}")
    with col2:
        # Get fan UID from either new or legacy structure
        fan_uid = None
        if "fan" in qd and isinstance(qd["fan"], dict):
            fan_uid = qd["fan"].get("uid")
        if fan_uid is None:
            fan_uid = qd.get('fan_uid', 'N/A')
            
        st.markdown(f"**Fan ID:** {fan_uid} mm")
    st.divider()
   
    # Motor Information (more detailed)
    st.subheader("Motor Information")
    
    # Get motor details from either new or legacy structure
    motor_details = None
    if "motor" in qd and isinstance(qd["motor"], dict) and "details" in qd["motor"]:
        motor_details = qd["motor"]["details"]
    else:
        motor_details = qd.get('selected_motor_details')
        
    if motor_details and isinstance(motor_details, dict):
        motor = motor_details
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Supplier:** {motor.get('supplier_name', 'N/A')}")
            st.markdown(f"**Product Range:** {motor.get('product_range', 'N/A')}")
            
            # Get mount type from either new or legacy structure
            mount_type = None
            if "motor" in qd and isinstance(qd["motor"], dict):
                mount_type = qd["motor"].get("mount_type")
            if mount_type is None:
                mount_type = qd.get('motor_mount_type', 'N/A')
                
            st.markdown(f"**Mount Type:** {mount_type}")
        with col2:
            st.markdown(f"**Power:** {motor.get('rated_output', 0)} {motor.get('rated_output_unit', 'kW')}")
            st.markdown(f"**Poles:** {motor.get('poles', 'N/A')}")
            st.markdown(f"**Speed:** {motor.get('speed', 'N/A')} {motor.get('speed_unit', 'RPM')}")
        with col3:
            # Get motor price, checking both structures
            motor_price = None
            if "motor" in qd and isinstance(qd["motor"], dict):
                motor_price = qd["motor"].get("price")
            if motor_price is None:
                motor_price = qd.get("motor_price")
            if motor_price is None:
                motor_price = 0
            
            try:
                base_price = float(motor_price)
                st.markdown(f"**Base Price:** {CURRENCY_SYMBOL} {base_price:,.2f}")
            except (ValueError, TypeError):
                st.markdown(f"**Base Price:** {CURRENCY_SYMBOL} 0.00")
            
            # Show markup details - get from new structure first, then fall back to legacy
            motor_markup_override = None
            if "motor" in qd and isinstance(qd["motor"], dict):
                motor_markup_override = qd["motor"].get("markup_override")
            if motor_markup_override is None:
                motor_markup_override = qd.get("motor_markup_override")
            if motor_markup_override is None:
                motor_markup_override = 1.0  # Default markup is 1.0 (no markup)
            
            try:
                # Try to convert to float (handle potential string values)
                motor_markup = float(motor_markup_override)
                motor_markup_pct = (motor_markup - 1) * 100
                st.markdown(f"**Markup Applied:** {motor_markup:.2f} ({motor_markup_pct:.1f}%)")
            except (ValueError, TypeError):
                st.markdown(f"**Markup Applied:** 1.00 (0.0%)")
            
            # Final price - get from new structure first, then fall back to legacy
            motor_price_after_markup = None
            if "motor" in qd and isinstance(qd["motor"], dict):
                motor_price_after_markup = qd["motor"].get("price_after_markup")
            if motor_price_after_markup is None:
                motor_price_after_markup = qd.get("motor_price_after_markup")
                
            if motor_price_after_markup is not None:
                try:
                    final_price = float(motor_price_after_markup)
                    st.markdown(f"**Final Price:** {CURRENCY_SYMBOL} {final_price:,.2f}")
                except (ValueError, TypeError):
                    # If conversion fails, don't show the final price
                    pass
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
    # Get motor details from either new or legacy structure
    motor_details = None
    if "motor" in qd and isinstance(qd["motor"], dict) and "details" in qd["motor"]:
        motor_details = qd["motor"]["details"]
    if motor_details is None:
        motor_details = qd.get('selected_motor_details')
    
    if motor_details and isinstance(motor_details, dict):
        motor = motor_details
        
        # Get motor price after markup from either new or legacy structure
        motor_price_after_markup = None
        if "motor" in qd and isinstance(qd["motor"], dict):
            motor_price_after_markup = qd["motor"].get("price_after_markup")
        if motor_price_after_markup is None:
            motor_price_after_markup = qd.get("motor_price_after_markup")
            
        try:
            motor_price = float(motor_price_after_markup or 0)
        except (ValueError, TypeError):
            motor_price = 0
        
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
    breakdown_rows.append({
        "Item Type": "Subtotal",
        "Item": "Buyout Items Subtotal (Future)",
        "Cost": 0
    })
    
    # Calculate and add Final Total
    components_total = server_summary.get("final_price", 0) or 0
    
    # Get motor price after markup from either new or legacy structure
    motor_price_after_markup = None
    if "motor" in qd and isinstance(qd["motor"], dict):
        motor_price_after_markup = qd["motor"].get("price_after_markup")
    if motor_price_after_markup is None:
        motor_price_after_markup = qd.get("motor_price_after_markup", 0)
        
    try:
        motor_total = float(motor_price_after_markup or 0)
    except (ValueError, TypeError):
        motor_total = 0
        
    buyout_total = 0  # For future implementation
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
        
        # Get values from either new or legacy structure
        quote_ref = None
        client_name = None
        project_name = None
        project_location = None
        
        if "project_info" in qd and isinstance(qd["project_info"], dict):
            quote_ref = qd["project_info"].get("quote_ref")
            client_name = qd["project_info"].get("client")
            project_name = qd["project_info"].get("name")
            project_location = qd["project_info"].get("location")
            
        # Fall back to legacy structure if needed
        if quote_ref is None:
            quote_ref = qd.get("quote_ref")
        if client_name is None:
            client_name = qd.get("client_name")
        if project_name is None:
            project_name = qd.get("project_name")
        if project_location is None:
            project_location = qd.get("project_location")
        
        # Prepare payload from session state
        payload = {
            "quote_ref": quote_ref,
            "client_name": client_name,
            "project_name": project_name,
            "project_location": project_location,
            "user_id": user_id,
            "quote_data": qd
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