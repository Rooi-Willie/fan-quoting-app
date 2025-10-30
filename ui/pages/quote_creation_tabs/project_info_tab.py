import streamlit as st

def render_main_content():
    st.header("1. Project Information")
    
    # Work with v3 schema structure
    qd = st.session_state.quote_data
    quote_section = qd.setdefault("quote", {})
    
    # Get dynamic widget key suffix for widget reset support
    widget_reset_counter = st.session_state.get("widget_reset_counter", 0)
    widget_key_suffix = f"_{widget_reset_counter}"

    cols = st.columns(2)
    with cols[0]:
        quote_section["project"] = st.text_input(
            "Project Name/Reference",
            value=quote_section.get("project", ""),
            key=f"widget_proj_name{widget_key_suffix}",
        )
        quote_section["client"] = st.text_input(
            "Client Name",
            value=quote_section.get("client", ""),
            key=f"widget_client_name{widget_key_suffix}",
        )
    with cols[1]:
        # Check if editing an existing quote - if so, make quote_ref read-only
        is_editing = st.session_state.get("editing_quote_id") is not None
        
        if is_editing:
            # Display as disabled input to show it's not editable
            st.text_input(
                "Our Quote Reference",
                value=quote_section.get("reference", ""),
                key=f"widget_quote_ref_us_disabled{widget_key_suffix}",
                disabled=True,
                help="Quote reference cannot be changed when editing to maintain revision history integrity"
            )
            # Keep the value in quote_section unchanged
        else:
            # Allow editing for new quotes
            quote_section["reference"] = st.text_input(
                "Our Quote Reference",
                value=quote_section.get("reference", ""),
                key=f"widget_quote_ref_us{widget_key_suffix}",
            )
        
        quote_section["location"] = st.text_input(
            "Project Location / Site",
            value=quote_section.get("location", ""),
            key=f"widget_proj_loc{widget_key_suffix}",
        )
    # Add more project info fields as needed
    quote_section["notes"] = st.text_area(
        "Project Notes / Scope",
        value=quote_section.get("notes", ""),
        key=f"widget_proj_notes{widget_key_suffix}",
        height=100,
    )