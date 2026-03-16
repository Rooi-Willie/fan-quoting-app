import streamlit as st
import requests
import datetime
import json
import os
from config import APP_TITLE
from common import _new_quote_data
from export_utils import generate_docx, generate_filename
from utils import get_api_headers

# API_BASE_URL should be configured, e.g., via environment variable
# Fallback is provided for local development.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8080")

# Page configuration
st.set_page_config(page_title=f"Quote Details - {APP_TITLE}", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("Please log in first through the main Login page.")
    if st.button("Go to Login"):
        st.switch_page("Login_Page.py")
    st.stop()

# Check if we have a quote ID to view
if "viewing_quote_id" not in st.session_state:
    st.error("No quote selected for viewing.")
    if st.button("Go to Quotes List"):
        st.switch_page("pages/3_View_Existing_Quotes.py")
    st.stop()

quote_id = st.session_state.viewing_quote_id

# Function to load quote details
def load_quote_details(quote_id):
    try:
        response = requests.get(f"{API_BASE_URL}/saved-quotes/{quote_id}", headers=get_api_headers())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error loading quote details: {str(e)}")
        return None

# Load quote
quote = load_quote_details(quote_id)
if not quote:
    st.error("Failed to load quote details.")
    if st.button("Go Back"):
        st.switch_page("pages/3_View_Existing_Quotes.py")
    st.stop()

# Modern header with status and navigation
st.markdown("""<style>
.quote-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 0.5rem;
    margin-bottom: 2rem;
    color: white;
}
.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.875rem;
    font-weight: 600;
    margin-left: 1rem;
}
.status-draft { background: #f59e0b; }
.status-sent { background: #3b82f6; }
.status-approved { background: #10b981; }
.status-rejected { background: #ef4444; }
</style>""", unsafe_allow_html=True)

# Header container
header_col1, header_col2, header_col3 = st.columns([3, 1, 1])
with header_col1:
    status_color = {
        "draft": "🟠",
        "sent": "🔵", 
        "approved": "🟢",
        "rejected": "🔴"
    }
    st.markdown(f"""<div class="quote-header">
        <h1 style="margin: 0; font-size: 2rem;">{quote['quote_ref']} 
        <span class="status-badge status-{quote['status'].lower()}">{status_color.get(quote['status'].lower(), '⚪')} {quote['status'].upper()}</span></h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Revision {quote['revision_number']} • Quote Details</p>
    </div>""", unsafe_allow_html=True)

with header_col3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to List", use_container_width=True, type="secondary"):
        st.switch_page("pages/3_View_Existing_Quotes.py")

# Project information section with enhanced cards
st.markdown("### 📋 Project Information")

creation_date = datetime.datetime.fromisoformat(quote['creation_date'].replace('Z', '+00:00'))
formatted_date = creation_date.strftime('%Y-%m-%d')

project_info_html = f"""<div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1rem;'>
<div style='background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); padding: 1.25rem; border-radius: 0.5rem; color: white;'>
<div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
<div style='background: rgba(255,255,255,0.2); width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; margin-right: 0.75rem;'>🏢</div>
<div style='flex: 1;'>
<p style='margin: 0; font-size: 0.75rem; opacity: 0.8; text-transform: uppercase;'>Client</p>
<p style='margin: 0.25rem 0 0 0; font-size: 1.1rem; font-weight: bold;'>{quote['client_name'] or 'Not specified'}</p>
</div>
</div>
</div>
<div style='background: linear-gradient(135deg, #ec4899 0%, #db2777 100%); padding: 1.25rem; border-radius: 0.5rem; color: white;'>
<div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
<div style='background: rgba(255,255,255,0.2); width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; margin-right: 0.75rem;'>📁</div>
<div style='flex: 1;'>
<p style='margin: 0; font-size: 0.75rem; opacity: 0.8; text-transform: uppercase;'>Project</p>
<p style='margin: 0.25rem 0 0 0; font-size: 1.1rem; font-weight: bold;'>{quote['project_name'] or 'Not specified'}</p>
</div>
</div>
</div>
<div style='background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%); padding: 1.25rem; border-radius: 0.5rem; color: white;'>
<div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
<div style='background: rgba(255,255,255,0.2); width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; margin-right: 0.75rem;'>📍</div>
<div style='flex: 1;'>
<p style='margin: 0; font-size: 0.75rem; opacity: 0.8; text-transform: uppercase;'>Location</p>
<p style='margin: 0.25rem 0 0 0; font-size: 1.1rem; font-weight: bold;'>{quote['project_location'] or 'Not specified'}</p>
</div>
</div>
</div>
<div style='background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 1.25rem; border-radius: 0.5rem; color: white;'>
<div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
<div style='background: rgba(255,255,255,0.2); width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; margin-right: 0.75rem;'>📅</div>
<div style='flex: 1;'>
<p style='margin: 0; font-size: 0.75rem; opacity: 0.8; text-transform: uppercase;'>Created</p>
<p style='margin: 0.25rem 0 0 0; font-size: 1.1rem; font-weight: bold;'>{formatted_date}</p>
</div>
</div>
</div>
</div>"""

st.markdown(project_info_html, unsafe_allow_html=True)

st.divider()

# Quote details from the saved JSON
quote_data = quote.get("quote_data") or {}

# User information section
meta = quote_data.get("meta", {})
created_by_user = meta.get("created_by_user")
last_modified_by_user = meta.get("last_modified_by_user")

if created_by_user or last_modified_by_user:
    st.markdown("### 👤 Quote History")
    
    user_info_cols = st.columns(2)
    
    # Created by information
    with user_info_cols[0]:
        if created_by_user:
            st.markdown("**Created By**")
            
            # User profile card
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 1rem; border-radius: 0.5rem; color: white;'>
                <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                    <div style='background: rgba(255,255,255,0.2); width: 48px; height: 48px; 
                                border-radius: 50%; display: flex; align-items: center; 
                                justify-content: center; font-size: 1.5rem; margin-right: 1rem;'>
                        👤
                    </div>
                    <div>
                        <h3 style='margin: 0; font-size: 1.2rem;'>{created_by_user.get('full_name', created_by_user.get('username', 'Unknown'))}</h3>
                        <p style='margin: 0; font-size: 0.875rem; opacity: 0.9;'>{created_by_user.get('job_title', '')} {('• ' + created_by_user.get('department', '')) if created_by_user.get('department') else ''}</p>
                    </div>
                </div>
                <div style='background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 0.375rem; margin-top: 0.5rem;'>
                    <p style='margin: 0; font-size: 0.875rem;'>
                        <strong>📧</strong> {created_by_user.get('email', 'N/A')}<br>
                        <strong>📞</strong> {created_by_user.get('phone', 'N/A')}<br>
                        <strong>🏷️</strong> Role: {created_by_user.get('role', 'user').title()}
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Fallback for legacy quotes
            created_by = meta.get("created_by", "Unknown")
            st.markdown(f"""
            <div style='background: #f3f4f6; padding: 1rem; border-radius: 0.5rem;'>
                <p style='margin: 0;'><strong>Created by:</strong> {created_by}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Last modified by information
    with user_info_cols[1]:
        if last_modified_by_user:
            st.markdown("**Last Modified By**")
            
            # Check if same user as creator
            is_same_user = (created_by_user and 
                          created_by_user.get('id') == last_modified_by_user.get('id'))
            
            if is_same_user:
                st.markdown(f"""
                <div style='background: #f3f4f6; padding: 1rem; border-radius: 0.5rem; 
                            display: flex; align-items: center; justify-content: center; height: 100%;'>
                    <p style='margin: 0; color: #6b7280; text-align: center;'>
                        <em>Same as creator</em>
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Different user modified the quote
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                            padding: 1rem; border-radius: 0.5rem; color: white;'>
                    <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                        <div style='background: rgba(255,255,255,0.2); width: 48px; height: 48px; 
                                    border-radius: 50%; display: flex; align-items: center; 
                                    justify-content: center; font-size: 1.5rem; margin-right: 1rem;'>
                            ✏️
                        </div>
                        <div>
                            <h3 style='margin: 0; font-size: 1.2rem;'>{last_modified_by_user.get('full_name', last_modified_by_user.get('username', 'Unknown'))}</h3>
                            <p style='margin: 0; font-size: 0.875rem; opacity: 0.9;'>{last_modified_by_user.get('job_title', '')} {('• ' + last_modified_by_user.get('department', '')) if last_modified_by_user.get('department') else ''}</p>
                        </div>
                    </div>
                    <div style='background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 0.375rem; margin-top: 0.5rem;'>
                        <p style='margin: 0; font-size: 0.875rem;'>
                            <strong>📧</strong> {last_modified_by_user.get('email', 'N/A')}<br>
                            <strong>📞</strong> {last_modified_by_user.get('phone', 'N/A')}<br>
                            <strong>🏷️</strong> Role: {last_modified_by_user.get('role', 'user').title()}
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='background: #f3f4f6; padding: 1rem; border-radius: 0.5rem; 
                        display: flex; align-items: center; justify-content: center; height: 100%;'>
                <p style='margin: 0; color: #6b7280; text-align: center;'>
                    <em>No modifications yet</em>
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()

# v4 schema: iterate over fan_configurations[]
fan_configurations = quote_data.get("fan_configurations", [])
is_multi_config = len(fan_configurations) > 1

from utils import build_summary_dataframe, get_ordered_component_names, build_ordered_component_rows

for cfg_idx, cfg in enumerate(fan_configurations):
    cfg_spec = cfg.get("specification", {})
    cfg_pricing = cfg.get("pricing", {})
    cfg_calc = cfg.get("calculations", {})
    cfg_quantity = cfg.get("quantity", 1)
    cfg_label = cfg.get("label", f"Fan Config {cfg_idx + 1}")
    qty_badge = f" (x{cfg_quantity})" if cfg_quantity > 1 else ""

    fan_node = cfg_spec.get("fan", {})
    fan_config = fan_node.get("fan_configuration", {})
    motor_node = cfg_spec.get("motor", {})
    components_node = cfg_spec.get("components", [])

    if is_multi_config:
        st.markdown(f"### {cfg_label}{qty_badge}")

    # Fan configuration section
    st.markdown("### ⚙️ Fan Configuration")

    config_id = fan_config.get("uid", "N/A")
    blade_sets = str(fan_node.get("blade_sets") or "N/A")
    fan_size = fan_config.get("fan_size_mm") or "N/A"
    hub_size = fan_config.get("hub_size_mm") or "N/A"
    component_markup = cfg_pricing.get('component_markup', 1.4)
    motor_markup = cfg_pricing.get('motor_markup', 1.2)

    fan_html = f"""<div style='background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 1.5rem; border-radius: 0.5rem; color: white; margin-bottom: 1rem;'>
<div style='display: flex; align-items: center; margin-bottom: 1rem;'>
<div style='background: rgba(255,255,255,0.2); width: 56px; height: 56px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2rem; margin-right: 1.5rem;'>⚙️</div>
<div><h3 style='margin: 0; font-size: 1.5rem;'>{config_id}</h3>
<p style='margin: 0; font-size: 0.875rem; opacity: 0.9;'>Fan Configuration{qty_badge}</p></div>
</div>
<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;'>
<div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 0.375rem;'>
<p style='margin: 0; font-size: 0.75rem; opacity: 0.8; text-transform: uppercase;'>Blade Sets</p>
<p style='margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: bold;'>{blade_sets}</p>
</div>
<div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 0.375rem;'>
<p style='margin: 0; font-size: 0.75rem; opacity: 0.8; text-transform: uppercase;'>Fan Size</p>
<p style='margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: bold;'>{fan_size}{'mm' if fan_size != 'N/A' else ''}</p>
</div>
<div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 0.375rem;'>
<p style='margin: 0; font-size: 0.75rem; opacity: 0.8; text-transform: uppercase;'>Hub Size</p>
<p style='margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: bold;'>{hub_size}{'mm' if hub_size != 'N/A' else ''}</p>
</div>
<div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 0.375rem;'>
<p style='margin: 0; font-size: 0.75rem; opacity: 0.8; text-transform: uppercase;'>Component Markup</p>
<p style='margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: bold;'>{((float(component_markup) - 1) * 100):.0f}%</p>
</div>
<div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 0.375rem;'>
<p style='margin: 0; font-size: 0.75rem; opacity: 0.8; text-transform: uppercase;'>Motor Markup</p>
<p style='margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: bold;'>{((float(motor_markup) - 1) * 100):.0f}%</p>
</div>
</div>
</div>"""

    st.markdown(fan_html, unsafe_allow_html=True)

    st.divider()

    # Motor information section
    motor_calc = cfg_calc.get("motor", {})
    if motor_node.get("motor_details") or motor_calc:
        st.markdown("### 🔌 Motor Information")
        motor = motor_node.get("motor_details", {})

        supplier = motor.get("supplier_name", "Not specified")
        mount_type = motor_node.get("mount_type", "Not specified")
        product_range = motor.get("product_range", "Not specified")
        output = motor.get("rated_output", "N/A")
        output_unit = motor.get("rated_output_unit", "")
        speed = motor.get("speed", "N/A")
        speed_unit = motor.get("speed_unit", "")
        poles = motor.get("poles", "N/A")
        base_price = motor_calc.get("base_price", 0)
        final_price = motor_calc.get("final_price", 0)
        markup_pct = (float(motor_markup) - 1) * 100

        motor_html = f"""<div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 1.5rem; border-radius: 0.5rem; color: white; margin-bottom: 1rem;'>
<div style='display: flex; align-items: center; margin-bottom: 1rem;'>
<div style='background: rgba(255,255,255,0.2); width: 56px; height: 56px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2rem; margin-right: 1.5rem;'>🔌</div>
<div><h3 style='margin: 0; font-size: 1.5rem;'>{supplier}</h3>
<p style='margin: 0; font-size: 0.875rem; opacity: 0.9;'>{product_range}</p></div>
</div>
<div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1rem;'>
<div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 0.375rem;'>
<p style='margin: 0; font-size: 0.75rem; opacity: 0.8; text-transform: uppercase;'>Mount Type</p>
<p style='margin: 0.25rem 0 0 0; font-size: 1.2rem; font-weight: bold;'>{mount_type}</p>
</div>
<div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 0.375rem;'>
<p style='margin: 0; font-size: 0.75rem; opacity: 0.8; text-transform: uppercase;'>Poles</p>
<p style='margin: 0.25rem 0 0 0; font-size: 1.2rem; font-weight: bold;'>{poles}</p>
</div>
<div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 0.375rem;'>
<p style='margin: 0; font-size: 0.75rem; opacity: 0.8; text-transform: uppercase;'>Rated Output</p>
<p style='margin: 0.25rem 0 0 0; font-size: 1.2rem; font-weight: bold;'>{output} {output_unit}</p>
</div>
<div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 0.375rem;'>
<p style='margin: 0; font-size: 0.75rem; opacity: 0.8; text-transform: uppercase;'>Speed</p>
<p style='margin: 0.25rem 0 0 0; font-size: 1.2rem; font-weight: bold;'>{speed} {speed_unit}</p>
</div>
</div>"""

        st.markdown(motor_html, unsafe_allow_html=True)

        discount_data = cfg_pricing.get('motor_supplier_discount', {})
        supplier_discount = discount_data.get('applied_discount', 0.0)

        if base_price > 0:
            pricing_html = f"""<div style='background: rgba(255,255,255,0.15); padding: 1rem; border-radius: 0.375rem;'>
<p style='margin: 0 0 0.5rem 0; font-size: 0.875rem; opacity: 0.9; font-weight: 600;'>PRICING BREAKDOWN</p>
<div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
<span>Base Price:</span>
<span style='font-weight: bold;'>R {float(base_price):,.2f}</span>
</div>"""

            if supplier_discount > 0:
                discount_multiplier = 1.0 - (supplier_discount / 100.0)
                discounted_price = float(base_price) * discount_multiplier
                pricing_html += f"""<div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
<span>Supplier Discount ({supplier_discount:.2f}%):</span>
<span style='font-weight: bold;'>R {discounted_price:,.2f}</span>
</div>"""

            pricing_html += f"""<div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
<span>Markup ({markup_pct:.0f}%):</span>
<span style='font-weight: bold;'>Applied</span>
</div>
<div style='border-top: 2px solid rgba(255,255,255,0.3); margin-top: 0.5rem; padding-top: 0.5rem;'>
<div style='display: flex; justify-content: space-between;'>
<span style='font-size: 1.1rem; font-weight: bold;'>Final Price:</span>
<span style='font-size: 1.3rem; font-weight: bold;'>R {float(final_price):,.2f}</span>
</div>
</div>
</div>"""
        else:
            pricing_html = f"""<div style='background: rgba(255,255,255,0.15); padding: 1rem; border-radius: 0.375rem;'>
<p style='margin: 0 0 0.5rem 0; font-size: 0.875rem; opacity: 0.9; font-weight: 600;'>PRICING</p>
<div style='display: flex; justify-content: space-between;'>
<span style='font-size: 1.1rem; font-weight: bold;'>Final Price:</span>
<span style='font-size: 1.3rem; font-weight: bold;'>R {float(final_price):,.2f}</span>
</div>
</div>"""

        st.markdown(pricing_html + "</div>", unsafe_allow_html=True)

        st.divider()

    # Components section
    if isinstance(components_node, list) and components_node:
        st.markdown("### 🔧 Component Breakdown")

        components_calc = cfg_calc.get("components", {})
        component_totals = cfg_calc.get("component_totals", {})

        if component_totals:
            summary_cols = st.columns(4)
            with summary_cols[0]:
                total_mass = component_totals.get("total_mass_kg", 0)
                st.metric("Total Mass", f"{float(total_mass):.2f} kg")
            with summary_cols[1]:
                mat_cost = component_totals.get("total_material_cost", 0)
                st.metric("Material Cost", f"R {float(mat_cost):,.2f}")
            with summary_cols[2]:
                lab_cost = component_totals.get("total_labour_cost", 0)
                st.metric("Labour Cost", f"R {float(lab_cost):,.2f}")
            with summary_cols[3]:
                comp_final = component_totals.get("final_price", 0)
                st.metric("Final Price", f"R {float(comp_final):,.2f}")

        st.markdown("**Fan Component Cost & Mass Summary**")

        if components_calc:
            ordered_names = get_ordered_component_names(cfg)
            rows = build_ordered_component_rows(components_calc, ordered_names)

            if rows:
                styler = build_summary_dataframe(rows, "R")
                st.write(styler)
            else:
                st.info("No components selected for this configuration.")
        else:
            st.info("No components selected for this configuration.")

        st.divider()

    # Buy-out items section for this config
    buyout_items_cfg = cfg_spec.get("buyouts", [])
    if buyout_items_cfg:
        st.markdown("### 📦 Buy-out Items")

        buyout_data = []
        total_buyout_cost = 0

        for item in buyout_items_cfg:
            subtotal = item.get("subtotal")
            if subtotal is None:
                unit_cost = float(item.get("unit_cost", item.get("cost", 0)))
                qty = float(item.get("qty", item.get("quantity", 0)))
                subtotal = unit_cost * qty

            total_buyout_cost += float(subtotal)

            buyout_data.append({
                "Description": item.get("description", "Unnamed item"),
                "Quantity": int(item.get("qty", item.get("quantity", 0))),
                "Unit Cost": f"R {float(item.get('unit_cost', item.get('cost', 0))):,.2f}",
                "Subtotal": f"R {float(subtotal):,.2f}",
                "Notes": item.get("notes", "")
            })

        st.metric("Total Buy-out Cost", f"R {total_buyout_cost:,.2f}")

        st.dataframe(
            buyout_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Description": st.column_config.TextColumn("Description", width="large"),
                "Quantity": st.column_config.NumberColumn("Qty", width="small"),
                "Unit Cost": st.column_config.TextColumn("Unit Cost", width="medium"),
                "Subtotal": st.column_config.TextColumn("Subtotal", width="medium"),
                "Notes": st.column_config.TextColumn("Notes", width="medium")
            }
        )

        st.divider()

    # Per-config line total (if quantity > 1)
    unit_total = cfg_calc.get("unit_total", 0)
    line_total = cfg_calc.get("line_total", 0)
    if cfg_quantity > 1:
        lt_cols = st.columns(2)
        with lt_cols[0]:
            st.metric("Unit Total (1 fan)", f"R {float(unit_total):,.2f}")
        with lt_cols[1]:
            st.metric(f"Line Total ({cfg_quantity} fans)", f"R {float(line_total):,.2f}")
        st.divider()

    if is_multi_config and cfg_idx < len(fan_configurations) - 1:
        st.markdown("---")

# Grand totals pricing summary
st.markdown("### 💰 Pricing Summary")

grand_totals = quote_data.get("grand_totals", {})
gt_components = float(grand_totals.get("components", 0))
gt_motors = float(grand_totals.get("motors", 0))
gt_buyouts = float(grand_totals.get("buyouts", 0))
gt_grand_total = float(grand_totals.get("grand_total", 0))
total_cost = quote.get('total_price') or gt_grand_total

cost_breakdown_cols = st.columns(4)

with cost_breakdown_cols[0]:
    st.markdown("**Components**")
    st.markdown(f"<div style='background: #f3f4f6; padding: 1rem; border-radius: 0.5rem; text-align: center;'>"
               f"<p style='font-size: 1.5rem; font-weight: bold; margin: 0; color: #3b82f6;'>R {gt_components:,.0f}</p>"
               f"</div>", unsafe_allow_html=True)

with cost_breakdown_cols[1]:
    st.markdown("**Motors**")
    st.markdown(f"<div style='background: #f3f4f6; padding: 1rem; border-radius: 0.5rem; text-align: center;'>"
               f"<p style='font-size: 1.5rem; font-weight: bold; margin: 0; color: #10b981;'>R {gt_motors:,.0f}</p>"
               f"</div>", unsafe_allow_html=True)

with cost_breakdown_cols[2]:
    st.markdown("**Buy-outs**")
    st.markdown(f"<div style='background: #f3f4f6; padding: 1rem; border-radius: 0.5rem; text-align: center;'>"
               f"<p style='font-size: 1.5rem; font-weight: bold; margin: 0; color: #f59e0b;'>R {gt_buyouts:,.0f}</p>"
               f"</div>", unsafe_allow_html=True)

with cost_breakdown_cols[3]:
    st.markdown("**Grand Total**")
    st.markdown(f"<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 0.5rem; text-align: center;'>"
               f"<p style='font-size: 1.8rem; font-weight: bold; margin: 0; color: white;'>R {float(total_cost):,.0f}</p>"
               f"<p style='margin: 0; color: rgba(255,255,255,0.8); font-size: 0.875rem;'>Final price</p>"
               f"</div>", unsafe_allow_html=True)
    
st.divider()

# Enhanced revision history
st.markdown("### 📋 Revision History")

try:
    response = requests.get(f"{API_BASE_URL}/saved-quotes/{quote['quote_ref']}/revisions", headers=get_api_headers())
    if response.status_code == 200:
        revisions = response.json()
        
        if len(revisions) > 1:
            # Timeline visualization for multiple revisions
            st.markdown("**Quote Timeline**")
            
            for i, rev in enumerate(reversed(revisions)):
                creation_date = datetime.datetime.fromisoformat(rev["creation_date"].replace("Z", "+00:00"))
                formatted_date = creation_date.strftime("%Y-%m-%d %H:%M")
                
                status_colors = {
                    "draft": "#f59e0b",
                    "sent": "#3b82f6", 
                    "approved": "#10b981",
                    "rejected": "#ef4444"
                }
                status_color = status_colors.get(rev["status"].lower(), "#6b7280")
                
                # Timeline item
                is_current = rev["id"] == quote["id"]
                border_style = "border-left: 4px solid #667eea" if is_current else "border-left: 4px solid #e5e7eb"
                
                st.markdown(f"""
                <div style="{border_style}; padding-left: 1rem; margin-bottom: 1rem; {'background: #f8fafc;' if is_current else ''}">
                    <div style="display: flex; justify-content: between; align-items: center;">
                        <h4 style="margin: 0; color: {'#1f2937' if is_current else '#6b7280'};">Rev {rev['revision_number']} {'(Current)' if is_current else ''}</h4>
                        <span style="background: {status_color}; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 600;">{rev['status'].upper()}</span>
                    </div>
                    <p style="margin: 0.25rem 0; color: #6b7280; font-size: 0.875rem;">{formatted_date}</p>
                    <p style="margin: 0; font-weight: 600; color: #1f2937;">R {rev.get('total_price', 0):,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("This is the first revision of this quote.")
            
except Exception as e:
    st.error(f"Error loading revision history: {str(e)}")

st.divider()

# Enhanced actions section
st.markdown("### ⚡ Actions")

action_cols = st.columns([2, 1, 1, 2])

with action_cols[0]:
    st.markdown("**Quote Management**")
    if st.button("✏️ Edit This Quote", use_container_width=True, type="primary"):
        st.session_state.quote_data = quote_data
        st.session_state.editing_quote_id = quote_id
        st.session_state.active_config_index = 0
        st.switch_page("pages/2_Create_New_Quote.py")
    
    # Download Word Document button
    try:
        docx_bytes = generate_docx(quote_data)
        filename = generate_filename(quote_data, extension="docx")
        
        st.download_button(
            label="📄 Download Word Document",
            data=docx_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    except FileNotFoundError as e:
        if st.button("📄 Download Word Document", use_container_width=True, disabled=True):
            pass
        st.error(f"Template not found. Please ensure quote_template.docx is in ui/templates/")
    except Exception as e:
        if st.button("📄 Download Word Document", use_container_width=True, disabled=True):
            pass
        st.error(f"Error: {str(e)}")
    
    # PDF placeholder button
    if st.button("📄 Download PDF (Coming Soon)", use_container_width=True, disabled=True):
        st.info("PDF export functionality will be implemented in a future update.")

with action_cols[1]:
    st.markdown("**Status**")
    current_status = quote["status"]
    
    # Status update with better UX
    status_options = ["draft", "sent", "approved", "rejected"]
    current_index = status_options.index(current_status) if current_status in status_options else 0
    
    new_status = st.selectbox(
        "Status",
        status_options,
        index=current_index,
        format_func=lambda x: f"{x.capitalize()}",
        key="status_selector"
    )

with action_cols[2]:
    st.markdown("**Update**")
    if st.button("💾 Save Status", use_container_width=True, disabled=(new_status == current_status)):
        try:
            response = requests.patch(
                f"{API_BASE_URL}/saved-quotes/{quote_id}/status", 
                json={"status": new_status},
                headers=get_api_headers()
            )
            response.raise_for_status()
            st.success(f"Status updated to {new_status.capitalize()}")
            st.rerun()
        except Exception as e:
            st.error(f"Error updating status: {str(e)}")

with action_cols[3]:
    st.markdown("**Versioning**")
    if st.button("🔄 Create New Revision", use_container_width=True):
        try:
            # Use logged-in user's ID
            user_id = st.session_state.get("user_id", 1)
            response = requests.post(
                f"{API_BASE_URL}/saved-quotes/{quote_id}/revise", 
                json={"user_id": user_id},
                headers=get_api_headers()
            )
            response.raise_for_status()
            new_revision = response.json()
            
            st.session_state.viewing_quote_id = new_revision["id"]
            st.success(f"Created revision {new_revision.get('revision_number', 'new')}")
            st.rerun()
        except Exception as e:
            st.error(f"Error creating revision: {str(e)}")