import streamlit as st
import requests
import datetime
import json
import os
from config import APP_TITLE
from pages.common import _new_v3_quote_data

# API_BASE_URL should be configured, e.g., via environment variable
# Fallback is provided for local development.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

# Page configuration
st.set_page_config(page_title=f"Quote Details - {APP_TITLE}", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("Please log in first through the main Login page.")
    if st.button("Go to Login"):
        st.switch_page("login_page.py")
    st.stop()

# Check if we have a quote ID to view
if "viewing_quote_id" not in st.session_state:
    st.error("No quote selected for viewing.")
    if st.button("Go to Quotes List"):
        st.switch_page("pages/3_View_Existing_Quotes.py")
    st.stop()

quote_id = st.session_state.viewing_quote_id

# Function to ensure v3 compatibility (v3 only)
def ensure_v3_compatibility(quote_data):
    """Return v3 quote data as-is, or return empty v3 structure if invalid."""
    if not isinstance(quote_data, dict):
        return _new_v3_quote_data()
    
    # Assume all data is v3 format
    return quote_data

# Function to load quote details
def load_quote_details(quote_id):
    try:
        response = requests.get(f"{API_BASE_URL}/saved-quotes/{quote_id}")
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
project_cols = st.columns(4)

with project_cols[0]:
    st.container()
    with st.container():
        st.markdown("**Client**")
        st.markdown(f"<p style='font-size: 1.2rem; margin: 0; color: white;'>{quote['client_name'] or 'Not specified'}</p>", unsafe_allow_html=True)

with project_cols[1]:
    st.container()
    with st.container():
        st.markdown("**Project**")
        st.markdown(f"<p style='font-size: 1.2rem; margin: 0; color: white;'>{quote['project_name'] or 'Not specified'}</p>", unsafe_allow_html=True)

with project_cols[2]:
    st.container()
    with st.container():
        st.markdown("**Location**")
        st.markdown(f"<p style='font-size: 1.2rem; margin: 0; color: white;'>{quote['project_location'] or 'Not specified'}</p>", unsafe_allow_html=True)
        
with project_cols[3]:
    st.container()
    with st.container():
        st.markdown("**Created**")
        creation_date = datetime.datetime.fromisoformat(quote['creation_date'].replace('Z', '+00:00'))
        st.markdown(f"<p style='font-size: 1.2rem; margin: 0; color: white;'>{creation_date.strftime('%Y-%m-%d')}</p>", unsafe_allow_html=True)

st.divider()

# Quote details from the saved JSON (v3 only)
quote_data = ensure_v3_compatibility(quote.get("quote_data") or {})

# Extract v3 schema data paths
fan_node = quote_data.get("specification", {}).get("fan", {})
calc_node = quote_data.get("calculations", {})
components_node = quote_data.get("specification", {}).get("components", [])
motor_node = quote_data.get("specification", {}).get("motor", {})

# Fan configuration section with enhanced display
st.markdown("### ⚙️ Fan Configuration")

# Fan overview card
with st.container():
    fan_overview_cols = st.columns([2, 1, 1, 1, 1])
    
    with fan_overview_cols[0]:
        st.markdown("**Fan Configuration**")
        config_id = fan_node.get("config_id") or fan_node.get("fan_configuration", {}).get("uid", "N/A")
        st.markdown(f"Configuration: <span style='color: #3b82f6; font-weight: bold;'>{config_id}</span>", unsafe_allow_html=True)
        blade_sets = str(fan_node.get("blade_sets") or "N/A")
        st.markdown(f"Blade sets: <span style='color: #10b981; font-weight: bold;'>{blade_sets}</span>", unsafe_allow_html=True)
        
    with fan_overview_cols[1]:
        st.markdown("**Fan Size**")
        fan_size = fan_node.get("fan_configuration", {}).get("fan_size_mm") or "N/A"
        st.markdown(f"<p style='font-size: 1.5rem; font-weight: bold; margin: 0; color: #3b82f6;'>{fan_size}</p>", unsafe_allow_html=True)
        if fan_size != "N/A":
            st.markdown("<p style='margin: 0; color: #6b7280;'>mm</p>", unsafe_allow_html=True)
    
    with fan_overview_cols[2]:
        st.markdown("**Hub Size**")
        hub_size = fan_node.get("fan_configuration", {}).get("hub_size_mm") or fan_node.get("hub_size_mm") or "N/A"
        st.markdown(f"<p style='font-size: 1.5rem; font-weight: bold; margin: 0; color: #10b981;'>{hub_size}</p>", unsafe_allow_html=True)
        if hub_size != "N/A":
            st.markdown("<p style='margin: 0; color: #6b7280;'>mm</p>", unsafe_allow_html=True)
        
    with fan_overview_cols[3]:
        st.markdown("**Component Markup**")
        component_markup = calc_node.get('component_markup') or quote.get('component_markup', 1.4)
        markup_pct = (float(component_markup) - 1) * 100
        st.markdown(f"<p style='font-size: 1.5rem; font-weight: bold; margin: 0; color: #f59e0b;'>{markup_pct:.0f}%</p>", unsafe_allow_html=True)
        
    with fan_overview_cols[4]:
        st.markdown("**Motor Markup**")
        motor_markup = calc_node.get('motor_markup') or quote.get('motor_markup', 1.2)
        markup_pct = (float(motor_markup) - 1) * 100
        st.markdown(f"<p style='font-size: 1.5rem; font-weight: bold; margin: 0; color: #8b5cf6;'>{markup_pct:.0f}%</p>", unsafe_allow_html=True)

st.divider()

# Motor information section
if motor_node.get("motor_details") or quote_data.get("calculations", {}).get("motor"):
    st.markdown("### 🔌 Motor Information")
    motor = motor_node.get("motor_details", {})
    motor_calc = quote_data.get("calculations", {}).get("motor", {})
    
    motor_main_cols = st.columns([2, 2])
    
    with motor_main_cols[0]:
        st.markdown("**Technical Specifications**")
        
        # Create a more organized layout with consistent spacing
        st.markdown("---")
            
        # Left column specs
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Supplier:**")
            supplier = motor.get("supplier_name", "Not specified")
            st.markdown(f"<div style='margin-bottom: 15px; padding-left: 10px;'>{supplier}</div>", unsafe_allow_html=True)
            
            st.markdown("**Mount Type:**")
            mount_type = motor_node.get("mount_type", "Not specified")
            st.markdown(f"<div style='margin-bottom: 15px; padding-left: 10px;'>{mount_type}</div>", unsafe_allow_html=True)
            
            st.markdown("**Product Range:**")
            product_range = motor.get("product_range", "Not specified")
            st.markdown(f"<div style='margin-bottom: 15px; padding-left: 10px;'>{product_range}</div>", unsafe_allow_html=True)
            
        with col2:
            st.markdown("**Rated Output:**")
            output = motor.get("rated_output", "N/A")
            output_unit = motor.get("rated_output_unit", "")
            st.markdown(f"<div style='margin-bottom: 15px; padding-left: 10px; font-weight: bold; color: #3b82f6;'>{output} {output_unit}</div>", unsafe_allow_html=True)
            
            st.markdown("**Speed:**")
            speed = motor.get("speed", "N/A")
            speed_unit = motor.get("speed_unit", "")
            st.markdown(f"<div style='margin-bottom: 15px; padding-left: 10px; font-weight: bold; color: #10b981;'>{speed} {speed_unit}</div>", unsafe_allow_html=True)
            
            st.markdown("**Pole:**")
            pole = motor.get("poles", "Not specified")
            st.markdown(f"<div style='margin-bottom: 15px; padding-left: 10px;'>{pole}</div>", unsafe_allow_html=True)
        
    with motor_main_cols[1]:
        st.markdown("**Pricing Breakdown**")
        st.markdown("---")
            
        base_price = motor_calc.get("base_price", 0)
        final_price = motor_calc.get("final_price", 0)
        motor_markup = quote.get('motor_markup', 1.2)
        markup_pct = (float(motor_markup) - 1) * 100
        
        if base_price > 0:
            st.markdown(f"**Base Price:** R {float(base_price):,.2f}")
            st.markdown(f"**Markup Applied:** {markup_pct:.0f}%")
            st.markdown(f"**Final Price:** <span style='font-size: 1.3rem; font-weight: bold; color: #10b981;'>R {float(final_price):,.2f}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"**Final Price:** <span style='font-size: 1.3rem; font-weight: bold; color: #10b981;'>R {float(final_price):,.2f}</span>", unsafe_allow_html=True)
            
        # Show additional motor details if available
        if motor.get("efficiency"):
            st.markdown(f"**Efficiency:** {motor['efficiency']}%")
    
    st.divider()

# Components section with enhanced details
# Handle v3 structure where components is a list
if isinstance(components_node, list) and components_node:
    st.markdown("### 🔧 Component Breakdown")
    
    components_calc = quote_data.get("calculations", {}).get("components", {})
    component_totals = quote_data.get("calculations", {}).get("component_totals", {})
    
    # Component summary card
    if component_totals:
        summary_cols = st.columns(4)
        with summary_cols[0]:
            total_mass = component_totals.get("total_mass_kg", 0)
            st.metric("Total Mass", f"{float(total_mass):.2f} kg")
        with summary_cols[1]:
            material_cost = component_totals.get("total_material_cost", 0)
            st.metric("Material Cost", f"R {float(material_cost):,.2f}")
        with summary_cols[2]:
            labour_cost = component_totals.get("total_labour_cost", 0)
            st.metric("Labour Cost", f"R {float(labour_cost):,.2f}")
        with summary_cols[3]:
            final_price = component_totals.get("final_price", 0)
            st.metric("Final Price", f"R {float(final_price):,.2f}")
    
    st.markdown("**Fan Component Cost & Mass Summary**")
    
    # Use the same table structure from review_quote_tab.py
    rows = []
    
    if components_calc:
        for comp_name, comp_calc in components_calc.items():
            rows.append({
                "Component": comp_calc.get("name", comp_name),
                "Length (mm)": comp_calc.get("total_length_mm"),
                "Real Mass (kg)": comp_calc.get("real_mass_kg"),
                "Material Cost": comp_calc.get("material_cost"),
                "Labour Cost": comp_calc.get("labour_cost"),
                "Cost Before Markup": comp_calc.get("total_cost_before_markup"),
                "Cost After Markup": comp_calc.get("total_cost_after_markup"),
            })
    
    if rows:
        # Use the build_summary_dataframe function to create a table with totals row
        from utils import build_summary_dataframe
        styler = build_summary_dataframe(rows, "R")
        st.write(styler)
    else:
        st.info("No components selected for this quote.")
    
    st.divider()

# Buy-out items section
buyout_items = quote_data.get("specification", {}).get("buyouts", [])
if not buyout_items:
    buyout_items = quote_data.get("buy_out_items", [])

if buyout_items:
    st.markdown("### 📦 Buy-out Items")
    
    buyout_data = []
    total_buyout_cost = 0
    
    for item in buyout_items:
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
    
    # Show total
    st.metric("Total Buy-out Cost", f"R {total_buyout_cost:,.2f}")
    
    # Enhanced buyout table
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

# Comprehensive pricing summary
st.markdown("### 💰 Pricing Summary")

# Get pricing data from various sources
server_summary = calc_node.get("server_summary", {})
component_totals = quote_data.get("calculations", {}).get("component_totals", {})
motor_calc = quote_data.get("calculations", {}).get("motor", {})
totals_section = quote_data.get("calculations", {}).get("totals", {})

# Calculate costs
component_cost = component_totals.get("final_price", 0) or server_summary.get("final_price", 0)
motor_cost = motor_calc.get("final_price", 0)
buyout_cost = sum([float(item.get("subtotal", 0)) for item in buyout_items])
total_cost = quote.get('total_price') or (float(component_cost) + float(motor_cost) + float(buyout_cost))

# Material and labour breakdown
material_cost = component_totals.get("total_material_cost", 0) or server_summary.get("total_material_cost", 0)
labour_cost = component_totals.get("total_labour_cost", 0) or server_summary.get("total_labour_cost", 0)
total_mass = component_totals.get("total_mass_kg", 0) or server_summary.get("total_real_mass_kg", 0) or server_summary.get("total_mass_kg", 0)

# Cost breakdown visualization
cost_breakdown_cols = st.columns(4)

with cost_breakdown_cols[0]:
    st.markdown("**Components**")
    comp_markup_display = quote.get('component_markup', 1.4)
    comp_markup_pct = (float(comp_markup_display) - 1) * 100
    st.markdown(f"<div style='background: #f3f4f6; padding: 1rem; border-radius: 0.5rem; text-align: center;'>"
               f"<p style='font-size: 1.5rem; font-weight: bold; margin: 0; color: #3b82f6;'>R {float(component_cost):,.0f}</p>"
               f"<p style='margin: 0; color: #6b7280; font-size: 0.875rem;'>+{comp_markup_pct:.0f}% markup</p>"
               f"</div>", unsafe_allow_html=True)

with cost_breakdown_cols[1]:
    st.markdown("**Motor**")
    motor_markup_display = quote.get('motor_markup', 1.2)
    motor_markup_pct = (float(motor_markup_display) - 1) * 100
    st.markdown(f"<div style='background: #f3f4f6; padding: 1rem; border-radius: 0.5rem; text-align: center;'>"
               f"<p style='font-size: 1.5rem; font-weight: bold; margin: 0; color: #10b981;'>R {float(motor_cost):,.0f}</p>"
               f"<p style='margin: 0; color: #6b7280; font-size: 0.875rem;'>+{motor_markup_pct:.0f}% markup</p>"
               f"</div>", unsafe_allow_html=True)

with cost_breakdown_cols[2]:
    st.markdown("**Buy-outs**")
    st.markdown(f"<div style='background: #f3f4f6; padding: 1rem; border-radius: 0.5rem; text-align: center;'>"
               f"<p style='font-size: 1.5rem; font-weight: bold; margin: 0; color: #f59e0b;'>R {float(buyout_cost):,.0f}</p>"
               f"<p style='margin: 0; color: #6b7280; font-size: 0.875rem;'>{len(buyout_items)} items</p>"
               f"</div>", unsafe_allow_html=True)

with cost_breakdown_cols[3]:
    st.markdown("**Total Quote**")
    st.markdown(f"<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 0.5rem; text-align: center;'>"
               f"<p style='font-size: 1.8rem; font-weight: bold; margin: 0; color: white;'>R {float(total_cost):,.0f}</p>"
               f"<p style='margin: 0; color: rgba(255,255,255,0.8); font-size: 0.875rem;'>Final price</p>"
               f"</div>", unsafe_allow_html=True)

# Cost breakdown details with improved colors for readability
st.markdown("**💰 Detailed Cost Breakdown**")

# Material and labour breakdown
cost_detail_cols = st.columns(2)

with cost_detail_cols[0]:
    st.markdown("**Material & Labour Costs**")
    if material_cost > 0 or labour_cost > 0:
        st.markdown(f"**Material Cost:** <span style='color: #10b981; font-weight: bold; float: right;'>R {float(material_cost):>8,.2f}</span>", unsafe_allow_html=True)
        st.markdown(f"**Labour Cost:** <span style='color: #f59e0b; font-weight: bold; float: right;'>R {float(labour_cost):>8,.2f}</span>", unsafe_allow_html=True)
        subtotal = float(material_cost) + float(labour_cost)
        st.markdown(f"**Subtotal:** <span style='color: #3b82f6; font-weight: bold; float: right;'>R {subtotal:>8,.2f}</span>", unsafe_allow_html=True)
    else:
        st.info("Detailed breakdown not available")

with cost_detail_cols[1]:
    st.markdown("**Markup Applied**")
    component_markup = quote.get('component_markup', 1.4)
    motor_markup = quote.get('motor_markup', 1.2)
    comp_markup_pct = (float(component_markup) - 1) * 100
    motor_markup_pct = (float(motor_markup) - 1) * 100
    
    st.markdown(f"**Component Markup:** <span style='color: #8b5cf6; font-weight: bold; float: right;'>{comp_markup_pct:>6.0f}%</span>", unsafe_allow_html=True)
    st.markdown(f"**Motor Markup:** <span style='color: #ef4444; font-weight: bold; float: right;'>{motor_markup_pct:>6.0f}%</span>", unsafe_allow_html=True)
    
st.divider()

# Enhanced revision history
st.markdown("### 📋 Revision History")

try:
    response = requests.get(f"{API_BASE_URL}/saved-quotes/{quote['quote_ref']}/revisions")
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
        # Load this quote for editing (migrated)
        st.session_state.quote_data = quote_data
        st.switch_page("pages/2_Create_New_Quote.py")
    
    if st.button("📄 Generate PDF", use_container_width=True):
        st.info("PDF generation functionality will be implemented")

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
                json={"status": new_status}
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
            response = requests.post(
                f"{API_BASE_URL}/saved-quotes/{quote_id}/revise", 
                json={"user_id": 1}
            )
            response.raise_for_status()
            new_revision = response.json()
            
            st.session_state.viewing_quote_id = new_revision["id"]
            st.success(f"Created revision {new_revision.get('revision_number', 'new')}")
            st.rerun()
        except Exception as e:
            st.error(f"Error creating revision: {str(e)}")