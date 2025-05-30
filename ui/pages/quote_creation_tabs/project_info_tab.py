import streamlit as st

def display_tab():
    st.header("1. Project Information")
    qd = st.session_state.quote_data # Shorthand

    cols = st.columns(2)
    with cols[0]:
        qd["project_name"] = st.text_input(
            "Project Name/Reference",
            value=qd.get("project_name", ""),
            key="proj_name"
        )
        qd["client_name"] = st.text_input(
            "Client Name",
            value=qd.get("client_name", ""),
            key="client_name"
        )
    with cols[1]:
        qd["quote_ref"] = st.text_input(
            "Our Quote Reference",
            value=qd.get("quote_ref", "Q" + st.session_state.get("username","demo")[0].upper() + "001"), # Auto-generate example
            key="quote_ref_us"
        )
        qd["project_location"] = st.text_input(
            "Project Location / Site",
            value=qd.get("project_location", ""),
            key="proj_loc"
        )
    # Add more project info fields as needed
    st.text_area("Project Notes / Scope", value=qd.get("project_notes", ""), key="proj_notes", height=100,
                 on_change=lambda: st.session_state.quote_data.update({"project_notes": st.session_state.proj_notes}))