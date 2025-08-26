import streamlit as st
from config import APP_TITLE
import logging

# Configure basic logging (optional, but good for quick setup)
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')

# Create a logger object
logger = logging.getLogger(__name__)

# Page Configuration (set for each page in 'pages' dir for consistency)
st.set_page_config(page_title=f"Home - {APP_TITLE}", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("Please log in first through the main Login page.")
    if st.button("Go to Login"):
        st.switch_page("login_page.py") # Path relative to the main app script
    st.stop()

# --- Sidebar for Home Page ---
st.sidebar.title(f"Welcome, {st.session_state.get('username', 'User')}!")
st.sidebar.divider()
st.sidebar.markdown("You are on the Home page.")
# Add any other home-specific sidebar items or links here if needed.

st.title("Home")
st.write(f"Welcome to the {APP_TITLE}, {st.session_state.get('username', 'User')}!")
st.divider()

st.subheader("What would you like to do?")

cols = st.columns(3)
with cols[0]:
    if st.button("🚀 Create New Quote", use_container_width=True):
        st.switch_page("pages/2_Create_New_Quote.py")

with cols[1]:
    if st.button("📄 View Existing Quotes", use_container_width=True):
        # st.switch_page("pages/3_View_Existing_Quotes.py") # Uncomment when ready
        st.info("View Existing Quotes feature is under development.")
        logger.debug("View Existing Quotes button clicked.")

# Add more options as needed in other columns or rows