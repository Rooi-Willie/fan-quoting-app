import streamlit as st
from config import APP_TITLE

st.set_page_config(page_title=f"View Quotes - {APP_TITLE}", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("Please log in first through the main Login page.")
    if st.button("Go to Login"):
        st.switch_page("login_page.py")
    st.stop()

st.title("View Existing Quotes")
st.info("This feature is under development. Saved quotes will be listed here.")
# Placeholder for future functionality (e.g., loading from a database or CSV)