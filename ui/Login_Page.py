import streamlit as st
import requests
import os
from dotenv import load_dotenv

from config import APP_TITLE

def check_password():
    """Returns `True` if the user had a correct password."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    if st.session_state.logged_in:
        return True

    # --- Password/User Database (Replace with secure method in production) ---
    # Option 1: Hardcoded (for demo only)
    VALID_USERS = {
        "demo": "demo",
        "user1": "pass1",
        # Add more users if needed
    }

    # Option 2: Using st.secrets (Recommended for deployment)
    # Ensure you have a secrets.toml file with:
    # [passwords]
    # demo = "demo_password_from_secret"
    # user1 = "user1_password_from_secret"
    #
    # valid_users_from_secrets = st.secrets.get("passwords", {})


    st.set_page_config(page_title=f"{APP_TITLE} - Login", layout="centered")
    st.title(f"{APP_TITLE} - Login")

    with st.form("login_form"):
        username = st.text_input("Username", key="login_username_main") # Unique key
        password = st.text_input("Password", type="password", key="login_password_main") # Unique key
        col1, col2 = st.columns(2)
        with col1:
            login_button = st.form_submit_button("Login", use_container_width=True)
        with col2:
            demo_button = st.form_submit_button("Login as Demo User", use_container_width=True)

        if login_button:
            # Use valid_users_from_secrets if using st.secrets
            if username in VALID_USERS and VALID_USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Incorrect username or password.")
        if demo_button:
            # Use valid_users_from_secrets if using st.secrets for demo user
            if "demo" in VALID_USERS and VALID_USERS["demo"] == "demo": # Check demo credentials
                st.session_state.logged_in = True
                st.session_state.username = "demo"
                st.rerun()
            else:
                st.error("Demo account credentials issue.") # Should not happen if VALID_USERS is correct
    return False


if not check_password():
    st.stop()

# --- If Logged In ---
# This part will only run if check_password() returns True
# Streamlit will automatically detect the 'pages' directory and build navigation.
# This page itself effectively becomes a redirect or a minimal welcome if users navigate back to it.
st.sidebar.success(f"Logged in as: {st.session_state.username}")
st.sidebar.divider()

st.header(f"Welcome, {st.session_state.username}!")
st.write(f"You are now logged into the {APP_TITLE}.")
st.write("Please select an option from the sidebar navigation to proceed.")
st.info("If you see other pages like 'Home' in the sidebar, login was successful and you can navigate there.")