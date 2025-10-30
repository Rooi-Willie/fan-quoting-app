import os
import streamlit as st
import pandas as pd
import requests
from config import APP_TITLE
import datetime
from common import _new_quote_data
from utils import get_api_headers

# API_BASE_URL should be configured, e.g., via environment variable
# Fallback is provided for local development.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8080")

# Page configuration
st.set_page_config(page_title=f"View Quotes - {APP_TITLE}", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("Please log in first through the main Login page.")
    if st.button("Go to Login"):
        st.switch_page("Login_Page.py")
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
        response = requests.get(f"{API_BASE_URL}/saved-quotes/", params=params, headers=get_api_headers())
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
        
        # Extract user information from summary fields
        created_by_name = q.get("created_by_user_name") or "-"
        last_modified_by_name = q.get("last_modified_by_user_name") or "-"
        
        # Create row with new column order
        df_data.append({
            "ID": q["id"],
            "Quote Ref": q["quote_ref"],
            "Client": q["client_name"],
            "Project": q["project_name"],
            "Date": formatted_date,
            "Fan": q["fan_uid"],
            "Motor": f"{q['motor_rated_output']} ({q['motor_supplier']})" if q["motor_rated_output"] else "-",
            "Price": f"R {q['total_price']:,.2f}" if q["total_price"] else "-",
            "Components": "\n".join([f"• {comp}" for comp in q["component_list"]]) if q.get("component_list") else "-",
            "Comp. Markup": f"{((q.get('component_markup', 1.0) - 1) * 100):.1f}%" if q.get("component_markup") else "-",
            "Motor Markup": f"{((q.get('motor_markup', 1.0) - 1) * 100):.1f}%" if q.get("motor_markup") else "-",
            "Status": q["status"].capitalize(),
            "Created By": created_by_name,
            "Last Mod. By": last_modified_by_name
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
            "Client": st.column_config.TextColumn("Client"),
            "Project": st.column_config.TextColumn("Project"),
            "Date": st.column_config.TextColumn("Date"),
            "Fan": st.column_config.TextColumn("Fan"),
            "Motor": st.column_config.TextColumn("Motor"),
            "Price": st.column_config.TextColumn("Price"),
            "Components": st.column_config.TextColumn("Components", width="medium", help="List of components in this quote"),
            "Comp. Markup": st.column_config.TextColumn("Comp. Markup"),
            "Motor Markup": st.column_config.TextColumn("Motor Markup"),
            "Status": st.column_config.TextColumn("Status"),
            "Created By": st.column_config.TextColumn("Created By"),
            "Last Mod. By": st.column_config.TextColumn("Last Mod. By")
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
                    response = requests.get(f"{API_BASE_URL}/saved-quotes/{quote_id}", headers=get_api_headers())
                    response.raise_for_status()
                    quote = response.json()
                    
                    # Set quote data in session state
                    qd_loaded = quote.get("quote_data") or {}
                    st.session_state.quote_data = qd_loaded
                    
                    # Store the quote ID for editing (enables UPDATE instead of CREATE)
                    st.session_state.editing_quote_id = quote_id
                    
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
                    # Use logged-in user's ID
                    user_id = st.session_state.get("user_id", 1)
                    response = requests.post(
                        f"{API_BASE_URL}/saved-quotes/{quote_id}/revise", 
                        json={"user_id": user_id}, 
                        headers=get_api_headers()
                    )
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
            # Reset specific quote data, keep login info (same as Reset Form button)
            logged_in_status = st.session_state.get("logged_in", False)
            user_data = {
                "user_id": st.session_state.get("user_id"),
                "username": st.session_state.get("username", ""),
                "full_name": st.session_state.get("full_name", ""),
                "email": st.session_state.get("email", ""),
                "phone": st.session_state.get("phone", ""),
                "department": st.session_state.get("department", ""),
                "job_title": st.session_state.get("job_title", ""),
                "user_role": st.session_state.get("user_role", "user"),
            }
            
            # Increment widget reset counter to force all widgets to recreate with new keys
            current_counter = st.session_state.get("widget_reset_counter", 0)
            
            st.session_state.clear()  # Clears everything
            
            # Restore login info
            st.session_state.logged_in = logged_in_status
            for key, value in user_data.items():
                st.session_state[key] = value
            st.session_state.widget_reset_counter = current_counter + 1  # Increment to force widget reset
            
            # Create fresh quote data with user session
            st.session_state.quote_data = _new_quote_data(
                username=user_data.get("username"),
                user_session=user_data if logged_in_status else None
            )
            
            # Redirect to quote creation page
            st.switch_page("pages/2_Create_New_Quote.py")