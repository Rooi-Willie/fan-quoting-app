"""
Enhanced Login Page with Database Integration
- Authenticates users against PostgreSQL users table
- Loads full user profile into session state
- Supports role-based access control
- Updates last_login timestamp
"""

import streamlit as st
import requests
import bcrypt
from datetime import datetime
from config import APP_TITLE, API_BASE_URL

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def authenticate_user(username: str, password: str) -> dict:
    """
    Authenticate user against database
    Returns user dict if successful, None otherwise
    """
    try:
        # Call API endpoint to get user by username
        response = requests.get(
            f"{API_BASE_URL}/users/by-username/{username}",
            timeout=5
        )
        
        if response.status_code == 404:
            return None
            
        response.raise_for_status()
        user = response.json()
        
        # Check if user is active
        if not user.get('is_active', False):
            st.error("Account is disabled. Please contact administrator.")
            return None
        
        # Verify password
        if verify_password(password, user['password_hash']):
            # Update last login
            update_last_login(user['id'])
            return user
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Authentication error: {str(e)}")
        return None

def update_last_login(user_id: int):
    """Update user's last login timestamp"""
    try:
        requests.patch(
            f"{API_BASE_URL}/users/{user_id}/last-login",
            timeout=5
        )
    except requests.exceptions.RequestException:
        pass  # Non-critical, don't block login

def load_user_session(user: dict):
    """Load user data into session state"""
    st.session_state.logged_in = True
    st.session_state.user_id = user['id']
    st.session_state.username = user['username']
    st.session_state.email = user['email']
    st.session_state.full_name = user.get('full_name', user['username'])
    st.session_state.phone = user.get('phone', '')
    st.session_state.department = user.get('department', '')
    st.session_state.job_title = user.get('job_title', '')
    st.session_state.user_role = user.get('role', 'user')

def check_password():
    """Returns `True` if the user had a correct password."""
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    st.set_page_config(page_title=f"{APP_TITLE} - Login", layout="centered")
    st.title(f"{APP_TITLE} - Login")
    
    st.info("🔒 **Security**: This app uses Streamlit's OAuth for initial access, plus database authentication for user tracking and role-based features.")

    with st.form("login_form"):
        username = st.text_input("Username", key="login_username_main")
        password = st.text_input("Password", type="password", key="login_password_main")
        
        col1, col2 = st.columns(2)
        with col1:
            login_button = st.form_submit_button("Login", use_container_width=True)
        with col2:
            demo_button = st.form_submit_button("Login as Demo User", use_container_width=True)

        if login_button:
            if username and password:
                user = authenticate_user(username, password)
                if user:
                    load_user_session(user)
                    st.success(f"Welcome back, {user.get('full_name', username)}!")
                    st.rerun()
                else:
                    st.error("❌ Incorrect username or password.")
            else:
                st.warning("Please enter both username and password.")
                
        if demo_button:
            # Demo user for testing
            user = authenticate_user("demo", "demo")
            if user:
                load_user_session(user)
                st.success(f"Welcome, Demo User!")
                st.rerun()
            else:
                st.error("Demo account not configured.")
                
    return False


if not check_password():
    st.stop()

# --- If Logged In ---
st.sidebar.success(f"👤 {st.session_state.full_name}")
st.sidebar.caption(f"Role: {st.session_state.user_role.title()}")
st.sidebar.divider()

st.header(f"Welcome, {st.session_state.full_name}!")
st.write(f"You are now logged into the {APP_TITLE}.")

# Display user info
col1, col2 = st.columns(2)
with col1:
    st.metric("Department", st.session_state.department or "Not set")
    st.metric("Email", st.session_state.email)
with col2:
    st.metric("Job Title", st.session_state.job_title or "Not set")
    st.metric("Phone", st.session_state.phone or "Not set")

st.divider()
st.info("📄 Please select an option from the sidebar navigation to proceed.")

# Role-based information
if st.session_state.user_role == 'admin':
    st.success("🔧 You have **Administrator** access to all features.")
elif st.session_state.user_role == 'engineer':
    st.info("⚙️ You have **Engineer** access - you can create and modify quotes.")
elif st.session_state.user_role == 'sales':
    st.info("💼 You have **Sales** access - you can create quotes and view reports.")
else:
    st.info("👁️ You have **Standard User** access.")
