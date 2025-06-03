import streamlit as st

def _update_quote_data_top_level_key(qd_top_level_key, widget_sstate_key):
    """
    Callback to update a key in st.session_state.quote_data
    from a widget's state in st.session_state.
    """
    if widget_sstate_key in st.session_state:
        st.session_state.quote_data[qd_top_level_key] = st.session_state[widget_sstate_key]

def display_tab():
    st.header("1. Project Information")
    qd = st.session_state.quote_data # Shorthand

    cols = st.columns(2)
    with cols[0]:
        st.text_input(
            "Project Name/Reference",
            value=qd.get("project_name", ""),
            key="widget_proj_name",
            on_change=_update_quote_data_top_level_key,
            args=("project_name", "widget_proj_name")
        )
        st.text_input(
            "Client Name",
            value=qd.get("client_name", ""),
            key="widget_client_name",
            on_change=_update_quote_data_top_level_key,
            args=("client_name", "widget_client_name")
        )
    with cols[1]:
        # For quote_ref, the initial value generation is fine, but updates should also use callback
        st.text_input(
            "Our Quote Reference",
            value=qd.get("quote_ref", "Q" + st.session_state.get("username","demo")[0].upper() + "001"), # Auto-generate example
            key="widget_quote_ref_us",
            on_change=_update_quote_data_top_level_key,
            args=("quote_ref", "widget_quote_ref_us")
        )
        st.text_input(
            "Project Location / Site",
            value=qd.get("project_location", ""),
            key="widget_proj_loc",
            on_change=_update_quote_data_top_level_key,
            args=("project_location", "widget_proj_loc")
        )
    # Add more project info fields as needed
    st.text_area("Project Notes / Scope",
                 value=qd.get("project_notes", ""),
                 key="widget_proj_notes", height=100,
                 on_change=_update_quote_data_top_level_key,
                 args=("project_notes", "widget_proj_notes")
                 )