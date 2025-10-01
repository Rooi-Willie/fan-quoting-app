import streamlit as st
from common import NEW_SCHEMA_VERSION

def render_main_content():
    st.header("1. Project Information")
    
    # Work with v3 schema structure
    qd = st.session_state.quote_data
    quote_section = qd.setdefault("quote", {})

    cols = st.columns(2)
    with cols[0]:
        quote_section["project"] = st.text_input(
            "Project Name/Reference",
            value=quote_section.get("project", ""),
            key="widget_proj_name",
        )
        quote_section["client"] = st.text_input(
            "Client Name",
            value=quote_section.get("client", ""),
            key="widget_client_name",
        )
    with cols[1]:
        quote_section["reference"] = st.text_input(
            "Our Quote Reference",
            value=quote_section.get("reference", ""),
            key="widget_quote_ref_us",
        )
        quote_section["location"] = st.text_input(
            "Project Location / Site",
            value=quote_section.get("location", ""),
            key="widget_proj_loc",
        )
    # Add more project info fields as needed
    quote_section["notes"] = st.text_area(
        "Project Notes / Scope",
        value=quote_section.get("notes", ""),
        key="widget_proj_notes",
        height=100,
    )