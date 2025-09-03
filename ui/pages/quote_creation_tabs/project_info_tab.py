import streamlit as st
from pages.quote_creation_tabs import shared_logic

def render_main_content():
    st.header("1. Project Information")
    
    # Initialize the new structure
    shared_logic.init_quote_data_structure()
    
    qd = st.session_state.quote_data
    project_info = qd.get("project_info", {})

    cols = st.columns(2)
    with cols[0]:
        st.text_input(
            "Project Name/Reference",
            value=project_info.get("name", ""),
            key="widget_proj_name",
            on_change=shared_logic.update_project_info,
            args=("name", "widget_proj_name")
        )
        st.text_input(
            "Client Name",
            value=project_info.get("client", ""),
            key="widget_client_name",
            on_change=shared_logic.update_project_info,
            args=("client", "widget_client_name")
        )
    with cols[1]:
        # For quote_ref, the initial value generation is handled by init_quote_data_structure
        st.text_input(
            "Our Quote Reference",
            value=project_info.get("quote_ref", ""),
            key="widget_quote_ref_us",
            on_change=shared_logic.update_project_info,
            args=("quote_ref", "widget_quote_ref_us")
        )
        st.text_input(
            "Project Location / Site",
            value=project_info.get("location", ""),
            key="widget_proj_loc",
            on_change=shared_logic.update_project_info,
            args=("location", "widget_proj_loc")
        )
        
    # Add more project info fields as needed
    st.text_area(
        "Project Notes / Scope",
        value=project_info.get("notes", ""),
        key="widget_proj_notes", 
        height=100,
        on_change=shared_logic.update_project_info,
        args=("notes", "widget_proj_notes")
    )