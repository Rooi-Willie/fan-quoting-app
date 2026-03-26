"""
User Management Page — Admin Only
Allows admins to list, create, edit, and deactivate users, and reset passwords.
"""

import streamlit as st
import pandas as pd
import requests
import logging
from config import APP_TITLE
from utils import api_get, api_post, api_patch, api_delete, API_BASE_URL, get_api_headers

logger = logging.getLogger(__name__)

st.set_page_config(page_title=f"User Management - {APP_TITLE}", layout="wide")

# --- Auth guard ---
if not st.session_state.get("logged_in"):
    st.warning("Please log in first through the main Login page.")
    if st.button("Go to Login"):
        st.switch_page("Login_Page.py")
    st.stop()

# --- Admin guard ---
if st.session_state.get("user_role") != "admin":
    st.error("Access denied. This page is for administrators only.")
    st.stop()

# --- Sidebar ---
st.sidebar.title(f"Welcome, {st.session_state.get('username', 'User')}!")
st.sidebar.divider()
st.sidebar.markdown("You are on the **User Management** page.")
st.sidebar.success("Admin access granted.")

# --- Page Header ---
st.title("User Management")

ROLE_OPTIONS = ["admin", "engineer", "sales", "user", "guest"]


def load_users(show_inactive: bool = False) -> list:
    """Fetch users from the API."""
    active_only = "false" if show_inactive else "true"
    result = api_get(f"/users/?active_only={active_only}&limit=500")
    return result if result else []


# ========================= TABS =========================
tab_list, tab_add = st.tabs(["User List", "Add New User"])

# ----------------------- TAB 1: User List -----------------------
with tab_list:
    show_inactive = st.toggle("Show inactive users", value=False, key="show_inactive_toggle")
    users = load_users(show_inactive)

    if not users:
        st.info("No users found.")
        st.stop()

    # Build display DataFrame (exclude password_hash)
    display_data = []
    for u in users:
        display_data.append({
            "ID": u["id"],
            "Username": u["username"],
            "Full Name": u.get("full_name") or "",
            "Email": u["email"],
            "Department": u.get("department") or "",
            "Job Title": u.get("job_title") or "",
            "Role": u.get("role", "user"),
            "Status": "Active" if u.get("is_active", True) else "Inactive",
            "Last Login": u.get("last_login") or "Never",
        })

    df = pd.DataFrame(display_data)

    # Dataframe with single-row selection
    event = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="user_table",
    )

    # Determine selected user
    selected_user = None
    selected_rows = event.selection.rows if event and event.selection else []
    if selected_rows:
        row_idx = selected_rows[0]
        selected_user_id = df.iloc[row_idx]["ID"]
        # Find matching user dict from the full API response
        for u in users:
            if u["id"] == selected_user_id:
                selected_user = u
                break

    if selected_user is None:
        st.info("Select a user from the table above to edit, reset password, or change status.")
    else:
        is_self = selected_user["id"] == st.session_state.get("user_id")

        st.subheader(f"Managing: {selected_user['username']}")
        if is_self:
            st.info("You cannot change your own role or deactivate your own account.")

        edit_col, pw_col, status_col = st.columns(3)

        # --- Edit User ---
        with edit_col:
            st.markdown("**Edit User Details**")
            with st.form("edit_user_form", clear_on_submit=False):
                new_email = st.text_input("Email", value=selected_user.get("email", ""))
                new_full_name = st.text_input("Full Name", value=selected_user.get("full_name") or "")
                new_phone = st.text_input("Phone", value=selected_user.get("phone") or "")
                new_department = st.text_input("Department", value=selected_user.get("department") or "")
                new_job_title = st.text_input("Job Title", value=selected_user.get("job_title") or "")

                current_role = selected_user.get("role", "user")
                role_idx = ROLE_OPTIONS.index(current_role) if current_role in ROLE_OPTIONS else 3
                new_role = st.selectbox(
                    "Role",
                    ROLE_OPTIONS,
                    index=role_idx,
                    disabled=is_self,
                )

                if st.form_submit_button("Save Changes"):
                    update_data = {
                        "email": new_email,
                        "full_name": new_full_name,
                        "phone": new_phone,
                        "department": new_department,
                        "job_title": new_job_title,
                    }
                    if not is_self:
                        update_data["role"] = new_role

                    result = api_patch(f"/users/{selected_user['id']}", update_data)
                    if result:
                        st.success("User updated successfully.")
                        st.rerun()

        # --- Reset Password ---
        with pw_col:
            st.markdown("**Reset Password**")
            with st.form("reset_password_form", clear_on_submit=True):
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")

                if st.form_submit_button("Reset Password"):
                    if not new_password:
                        st.error("Password cannot be empty.")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            response = requests.patch(
                                f"{API_BASE_URL}/users/{selected_user['id']}/reset-password",
                                json={"new_password": new_password},
                                headers=get_api_headers(),
                            )
                            response.raise_for_status()
                            st.success("Password reset successfully.")
                        except requests.exceptions.RequestException as e:
                            logger.error(f"Password reset failed: {e}")
                            st.error(f"Failed to reset password: {e}")

        # --- Activate / Deactivate ---
        with status_col:
            st.markdown("**Account Status**")
            if selected_user.get("is_active", True):
                st.success("This user is **active**.")
                if st.button(
                    "Deactivate User",
                    disabled=is_self,
                    use_container_width=True,
                    key="deactivate_btn",
                ):
                    result = api_delete(f"/users/{selected_user['id']}")
                    if result:
                        st.success("User deactivated.")
                        st.rerun()
            else:
                st.warning("This user is **inactive**.")
                if st.button(
                    "Reactivate User",
                    type="primary",
                    use_container_width=True,
                    key="reactivate_btn",
                ):
                    result = api_patch(
                        f"/users/{selected_user['id']}",
                        {"is_active": True},
                    )
                    if result:
                        st.success("User reactivated.")
                        st.rerun()

# ----------------------- TAB 2: Add New User -----------------------
with tab_add:
    st.markdown("Create a new user account.")

    with st.form("add_user_form", clear_on_submit=True):
        col_left, col_right = st.columns(2)

        with col_left:
            new_username = st.text_input("Username *")
            new_user_email = st.text_input("Email *")
            new_user_password = st.text_input("Password *", type="password")
            new_user_confirm = st.text_input("Confirm Password *", type="password")

        with col_right:
            new_user_full_name = st.text_input("Full Name")
            new_user_phone = st.text_input("Phone")
            new_user_department = st.text_input("Department")
            new_user_job_title = st.text_input("Job Title")
            new_user_role = st.selectbox("Role", ROLE_OPTIONS, index=3)

        submitted = st.form_submit_button("Create User", type="primary")

        if submitted:
            # Validation
            errors = []
            if not new_username.strip():
                errors.append("Username is required.")
            if not new_user_email.strip():
                errors.append("Email is required.")
            if not new_user_password:
                errors.append("Password is required.")
            elif len(new_user_password) < 8:
                errors.append("Password must be at least 8 characters.")
            elif new_user_password != new_user_confirm:
                errors.append("Passwords do not match.")

            if errors:
                for err in errors:
                    st.error(err)
            else:
                user_data = {
                    "username": new_username.strip(),
                    "email": new_user_email.strip(),
                    "password": new_user_password,
                    "full_name": new_user_full_name.strip() or None,
                    "phone": new_user_phone.strip() or None,
                    "department": new_user_department.strip() or None,
                    "job_title": new_user_job_title.strip() or None,
                    "role": new_user_role,
                }
                result = api_post("/users/", user_data)
                if result:
                    st.success(
                        f"User **{new_username}** created successfully "
                        f"(role: {new_user_role})."
                    )
