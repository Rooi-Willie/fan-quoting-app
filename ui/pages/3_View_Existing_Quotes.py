import os
import streamlit as st
import pandas as pd
import requests
from config import APP_TITLE
import datetime
from pages.common import _new_v3_quote_data

# API_BASE_URL should be configured, e.g., via environment variable
# Fallback is provided for local development.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

# Function to handle v2/v3 quote data compatibility
def ensure_v3_compatibility(quote_data):
    """Convert v2 quote data to v3 structure for display, or return v3 as-is."""
    if not isinstance(quote_data, dict):
        return _new_v3_quote_data()
    
    # Check if it's already v3
    if quote_data.get("meta", {}).get("version") == 3:
        return quote_data
    
    # If it's v2 or unversioned, create v3 structure with available data
    # This is a simplified conversion for display purposes only
    v3_data = _new_v3_quote_data()
    
    # Map v2 fields to v3 structure
    if "fan" in quote_data:
        v3_data["specification"]["fan"] = quote_data["fan"]
    if "motor" in quote_data and "selection" in quote_data["motor"]:
        v3_data["specification"]["motor"] = quote_data["motor"]["selection"]
        if "final_price" in quote_data["motor"]:
            v3_data["pricing"]["motor"]["final_price"] = quote_data["motor"]["final_price"]
    if "components" in quote_data and "selected" in quote_data["components"]:
        v3_data["specification"]["components"] = quote_data["components"]["selected"]
    if "buy_out_items" in quote_data:
        v3_data["specification"]["buyouts"] = quote_data["buy_out_items"]
    if "calculation" in quote_data:
        v3_data["calculations"] = quote_data["calculation"]
    
    return v3_data

# Page configuration
st.set_page_config(page_title=f"View Quotes - {APP_TITLE}", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("Please log in first through the main Login page.")
    if st.button("Go to Login"):
        st.switch_page("login_page.py")
    st.stop()

st.title("View Existing Quotes")

# Add filters at the top
with st.expander("Filters", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        client_filter = st.text_input("Client Name")
    
    with col2:
        status_options = ["All", "Draft", "Sent", "Approved", "Rejected"]
        status_filter = st.selectbox("Status", status_options)
    
    with col3:
        date_range = st.date_input(
            "Date Range",
            value=(
                datetime.datetime.now() - datetime.timedelta(days=30),
                datetime.datetime.now()
            ),
            max_value=datetime.datetime.now()
        )

# Function to load quotes
def load_quotes():
    try:
        # Build query parameters
        params = {}
        if client_filter:
            params["client_name"] = client_filter
        
        # Call API
        response = requests.get(f"{API_BASE_URL}/saved-quotes/", params=params)
        response.raise_for_status()
        quotes = response.json()
        
        # Apply additional filtering (status and date filters)
        if status_filter != "All":
            quotes = [q for q in quotes if q["status"].lower() == status_filter.lower()]
        
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            start_date = datetime.datetime.combine(start_date, datetime.time.min)
            end_date = datetime.datetime.combine(end_date, datetime.time.max)
            
            quotes = [
                q for q in quotes 
                if start_date <= datetime.datetime.fromisoformat(q["creation_date"].replace("Z", "+00:00")) <= end_date
            ]
        
        return quotes
    except Exception as e:
        st.error(f"Error loading quotes: {str(e)}")
        return []

# Load quotes on page load
quotes = load_quotes()

# Add refresh button
if st.button("🔄 Refresh"):
    quotes = load_quotes()
    st.success("Quote list refreshed")

# Display quotes in a table
if not quotes:
    st.info("No quotes found. Create a new quote to get started.")
else:
    # Convert to DataFrame for display
    df_data = []
    for q in quotes:
        # Format creation date
        creation_date = datetime.datetime.fromisoformat(q["creation_date"].replace("Z", "+00:00"))
        formatted_date = creation_date.strftime("%Y-%m-%d %H:%M")
        
        # Create row
        df_data.append({
            "ID": q["id"],
            "Quote Ref": q["quote_ref"],
            "Rev": q["revision_number"],
            "Client": q["client_name"],
            "Project": q["project_name"],
            "Fan": q["fan_uid"],
            "Size": f"{q['fan_size_mm']}mm" if q["fan_size_mm"] else "-",
            "Motor": f"{q['motor_rated_output']} ({q['motor_supplier']})" if q["motor_rated_output"] else "-",
            "Price": f"R {q['total_price']:,.2f}" if q["total_price"] else "-",
            "Status": q["status"].capitalize(),
            "Date": formatted_date
        })
    
    df = pd.DataFrame(df_data)
    
    # Display table with selection
    # Initialize selected_row in session state if not present
    if 'selected_row' not in st.session_state:
        st.session_state.selected_row = None
    
    # Use the same approach as in motor_selection_tab.py
    st.dataframe(
        df,
        key="quotes_selection_df",
        column_config={
            "ID": st.column_config.NumberColumn(format="%d"),
            "Quote Ref": st.column_config.TextColumn("Quote Ref"),
            "Rev": st.column_config.NumberColumn("Rev", format="%d"),
            "Client": st.column_config.TextColumn("Client"),
            "Project": st.column_config.TextColumn("Project"),
            "Fan": st.column_config.TextColumn("Fan"),
            "Size": st.column_config.TextColumn("Size"),
            "Motor": st.column_config.TextColumn("Motor"),
            "Price": st.column_config.TextColumn("Price"),
            "Status": st.column_config.TextColumn("Status"),
            "Date": st.column_config.TextColumn("Date")
        },
        on_select="rerun",  # Rerun the script when a row is selected
        selection_mode="single-row",  # Allow single row selection
        use_container_width=True,
        hide_index=True
    )
    
    # Process the selection when it changes (same approach as in motor_selection_tab.py)
    selection = st.session_state.get("quotes_selection_df", {}).get("selection", {})
    if selection.get("rows"):
        selected_index = selection["rows"][0]
        st.session_state.selected_row = df.iloc[selected_index].to_dict()
    
    
    # Show currently selected quote
    if st.session_state.selected_row is not None:
        col_info, col_clear = st.columns([5, 1])
        with col_info:
            st.success(f"Selected Quote: {st.session_state.selected_row['Quote Ref']} (ID: {st.session_state.selected_row['ID']})")
        with col_clear:
            if st.button("Clear Selection"):
                st.session_state.selected_row = None
                st.rerun()
    
    # Action buttons below the table
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("View Quote", use_container_width=True):
            # Get selected row (if any)
            if "selected_row" in st.session_state and st.session_state.selected_row is not None:
                quote_id = st.session_state.selected_row["ID"]
                st.session_state["viewing_quote_id"] = quote_id
                st.switch_page("pages/4_View_Quote_Details.py")
            else:
                st.warning("Please select a quote to view.")
    
    with col2:
        if st.button("Edit Quote", use_container_width=True):
            # Check if a row is selected
            if "selected_row" in st.session_state and st.session_state.selected_row is not None:
                quote_id = st.session_state.selected_row["ID"]
                
                # Load quote data into session
                try:
                    response = requests.get(f"{API_BASE_URL}/saved-quotes/{quote_id}")
                    response.raise_for_status()
                    quote = response.json()
                    
                    # Set quote data in session state (migrate if needed)
                    qd_loaded = quote.get("quote_data") or {}
                    st.session_state.quote_data = ensure_v3_compatibility(qd_loaded)
                    
                    # Redirect to quote creation page
                    st.switch_page("pages/2_Create_New_Quote.py")
                except Exception as e:
                    st.error(f"Error loading quote for editing: {str(e)}")
            else:
                st.warning("Please select a quote to edit.")
    
    with col3:
        if st.button("Create New Revision", use_container_width=True):
            # Check if a row is selected
            if "selected_row" in st.session_state and st.session_state.selected_row is not None:
                quote_id = st.session_state.selected_row["ID"]
                
                # Create new revision
                try:
                    # Using user_id 1 for development
                    response = requests.post(f"{API_BASE_URL}/saved-quotes/{quote_id}/revise", json={"user_id": 1})
                    response.raise_for_status()
                    
                    # Refresh quotes list
                    quotes = load_quotes()
                    st.success("New revision created successfully.")
                except Exception as e:
                    st.error(f"Error creating revision: {str(e)}")
            else:
                st.warning("Please select a quote to create a new revision.")
    
    with col4:
        if st.button("Create New Quote", use_container_width=True):
            # Clear existing quote data
            if "quote_data" in st.session_state:
                del st.session_state.quote_data
            
            # Redirect to quote creation page
            st.switch_page("pages/2_Create_New_Quote.py")