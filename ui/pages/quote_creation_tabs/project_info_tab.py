import streamlit as st
from pages.common import migrate_flat_to_nested_if_needed, NEW_SCHEMA_VERSION

def render_main_content():
    st.header("1. Project Information")
    # Ensure migrated (in case tab accessed directly after legacy load)
    st.session_state.quote_data = migrate_flat_to_nested_if_needed(st.session_state.quote_data)
    qd = st.session_state.quote_data
    proj = qd.setdefault("project", {})

    cols = st.columns(2)
    with cols[0]:
        proj["name"] = st.text_input(
            "Project Name/Reference",
            value=proj.get("name", ""),
            key="widget_proj_name",
        )
        proj["client"] = st.text_input(
            "Client Name",
            value=proj.get("client", ""),
            key="widget_client_name",
        )
    with cols[1]:
        proj["reference"] = st.text_input(
            "Our Quote Reference",
            value=proj.get("reference", qd.get("project", {}).get("reference", "")),
            key="widget_quote_ref_us",
        )
        proj["location"] = st.text_input(
            "Project Location / Site",
            value=proj.get("location", ""),
            key="widget_proj_loc",
        )
    # Add more project info fields as needed
    proj["notes"] = st.text_area(
        "Project Notes / Scope",
        value=proj.get("notes", ""),
        key="widget_proj_notes",
        height=100,
    )