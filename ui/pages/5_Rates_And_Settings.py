import streamlit as st
import pandas as pd
from config import APP_TITLE
from utils import api_get, api_patch
import logging

logger = logging.getLogger(__name__)

st.set_page_config(page_title=f"Rates & Settings - {APP_TITLE}", layout="wide")

# --- Auth guard: must be logged in ---
if not st.session_state.get("logged_in"):
    st.warning("Please log in first through the main Login page.")
    if st.button("Go to Login"):
        st.switch_page("Login_Page.py")
    st.stop()

# --- Determine admin status ---
is_admin = st.session_state.get("user_role") == "admin"
user_id = st.session_state.get("user_id")
username = st.session_state.get("username")

# --- Sidebar ---
st.sidebar.title(f"Welcome, {st.session_state.get('username', 'User')}!")
st.sidebar.divider()
st.sidebar.markdown("You are on the Rates & Settings page.")
if is_admin:
    st.sidebar.success("Admin access — you can edit values.")
else:
    st.sidebar.info("View-only access.")

# --- Page Header ---
st.title("Rates & Settings")

if is_admin:
    st.warning(
        "Changes made here affect cost calculations for **all future quotes**. "
        "Existing saved quotes retain the rates from when they were created. "
        "However, if an existing quote is opened for editing and recalculated, "
        "it will use the current rates.",
        icon="⚠️"
    )
else:
    st.info("You have view-only access to this page. Contact an administrator to make changes.")

st.divider()


# ========================= SECTION 1: GLOBAL SETTINGS =========================

st.subheader("Global Settings")

global_settings = api_get("/settings/global")

if global_settings:
    if is_admin:
        for setting_name, setting_value in global_settings.items():
            with st.expander(f"{setting_name}: {setting_value}", expanded=False):
                with st.form(key=f"global_setting_form_{setting_name}"):
                    new_value = st.number_input(
                        "Value",
                        min_value=0.01,
                        value=float(setting_value) if setting_value else 1.0,
                        format="%.4f",
                        key=f"global_setting_input_{setting_name}"
                    )

                    submitted = st.form_submit_button("Save")
                    if submitted:
                        if new_value <= 0:
                            st.error("Value must be a positive number.")
                        else:
                            result = api_patch(
                                f"/settings/global/{setting_name}?user_id={user_id}&username={username}",
                                {"setting_value": str(new_value)}
                            )
                            if result:
                                st.success(f"Setting '{setting_name}' updated to {new_value}.")
                                st.rerun()
    else:
        rows = [{"Setting": k, "Value": v} for k, v in global_settings.items()]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("Unable to load global settings.")

st.divider()


# ========================= SECTION 2: LABOUR RATES =========================

st.subheader("Labour Rates")

labour_rates = api_get("/settings/labour-rates")

if labour_rates:
    for rate in labour_rates:
        current_rate_per_hour = float(rate["rate_per_hour"])
        current_productivity = float(rate["productivity_kg_per_day"]) if rate.get("productivity_kg_per_day") else 0.0
        currency = rate.get("currency", "ZAR")

        label = f"{rate['rate_name']} — {currency} {current_rate_per_hour:.2f}/hr"
        if current_productivity > 0:
            label += f", {current_productivity:.2f} kg/day"

        with st.expander(label, expanded=False):
            if is_admin:
                with st.form(key=f"labour_rate_form_{rate['id']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_rate_per_hour = st.number_input(
                            f"Rate Per Hour ({currency}/hr)",
                            min_value=0.01,
                            value=current_rate_per_hour,
                            step=1.0,
                            format="%.2f",
                            key=f"rate_per_hour_{rate['id']}"
                        )
                    with col2:
                        new_productivity = st.number_input(
                            "Productivity (kg/day)",
                            min_value=0.0,
                            value=current_productivity,
                            step=1.0,
                            format="%.2f",
                            key=f"productivity_{rate['id']}",
                            help="Set to 0 if not applicable."
                        )

                    submitted = st.form_submit_button("Save Labour Rate")
                    if submitted:
                        if new_rate_per_hour <= 0:
                            st.error("Rate per hour must be greater than zero.")
                        else:
                            payload = {
                                "rate_per_hour": new_rate_per_hour,
                                "productivity_kg_per_day": new_productivity if new_productivity > 0 else None
                            }
                            result = api_patch(
                                f"/settings/labour-rates/{rate['id']}?user_id={user_id}&username={username}",
                                payload
                            )
                            if result:
                                st.success(f"Labour rate '{rate['rate_name']}' updated successfully.")
                                st.rerun()
            else:
                col1, col2, col3 = st.columns(3)
                col1.metric("Rate Per Hour", f"{currency} {current_rate_per_hour:.2f}")
                col2.metric("Productivity (kg/day)", f"{current_productivity:.2f}" if current_productivity > 0 else "N/A")
                col3.metric("Currency", currency)
else:
    st.info("Unable to load labour rates.")

st.divider()


# ========================= SECTION 3: MATERIAL COSTS =========================

st.subheader("Material Costs")

materials = api_get("/settings/materials")

if materials:
    for mat in materials:
        current_cost = float(mat["cost_per_unit"])
        cost_unit = mat.get("cost_unit", "unit")
        currency = mat.get("currency", "ZAR")

        label = f"{mat['name']} — {currency} {current_cost:.2f}/{cost_unit}"

        with st.expander(label, expanded=False):
            if mat.get("description"):
                st.caption(mat["description"])

            if is_admin:
                with st.form(key=f"material_form_{mat['id']}"):
                    new_cost = st.number_input(
                        f"Cost per {cost_unit} ({currency})",
                        min_value=0.01,
                        value=current_cost,
                        step=0.50,
                        format="%.2f",
                        key=f"cost_per_unit_{mat['id']}"
                    )

                    submitted = st.form_submit_button("Save Material Cost")
                    if submitted:
                        if new_cost <= 0:
                            st.error("Cost must be a positive number.")
                        else:
                            result = api_patch(
                                f"/settings/materials/{mat['id']}?user_id={user_id}&username={username}",
                                {"cost_per_unit": new_cost}
                            )
                            if result:
                                st.success(f"Material '{mat['name']}' cost updated to {currency} {new_cost:.2f}.")
                                st.rerun()
            else:
                col1, col2 = st.columns(2)
                col1.metric("Cost per Unit", f"{currency} {current_cost:.2f}/{cost_unit}")
                col2.metric("Currency", currency)
else:
    st.info("Unable to load materials.")

st.divider()


# =================== SECTION 4: MOTOR SUPPLIER DISCOUNTS ===================

st.subheader("Motor Supplier Discounts")

discounts = api_get("/settings/motor-supplier-discounts")

if discounts:
    if is_admin:
        for disc in discounts:
            current_pct = float(disc["discount_percentage"])
            is_active = disc.get("is_active", True)
            status = "Active" if is_active else "Inactive"

            label = f"{disc['supplier_name']} — {current_pct:.2f}% ({status}, effective {disc['date_effective']})"

            with st.expander(label, expanded=False):
                if disc.get("notes"):
                    st.caption(disc["notes"])

                with st.form(key=f"discount_form_{disc['id']}"):
                    new_pct = st.number_input(
                        "Discount Percentage (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=current_pct,
                        step=0.5,
                        format="%.2f",
                        key=f"discount_pct_{disc['id']}"
                    )

                    submitted = st.form_submit_button("Save Discount")
                    if submitted:
                        if new_pct < 0 or new_pct > 100:
                            st.error("Discount must be between 0% and 100%.")
                        else:
                            result = api_patch(
                                f"/settings/motor-supplier-discounts/{disc['id']}?user_id={user_id}&username={username}",
                                {"discount_percentage": new_pct}
                            )
                            if result:
                                st.success(f"Discount for '{disc['supplier_name']}' updated to {new_pct:.2f}%.")
                                st.rerun()
    else:
        df_data = []
        for d in discounts:
            df_data.append({
                "Supplier": d["supplier_name"],
                "Discount %": f"{float(d['discount_percentage']):.2f}%",
                "Effective Date": d["date_effective"],
                "Active": "Yes" if d.get("is_active") else "No",
                "Currency": d.get("currency", "ZAR"),
                "Notes": d.get("notes") or ""
            })
        st.dataframe(pd.DataFrame(df_data), use_container_width=True, hide_index=True)
else:
    st.info("No motor supplier discount records found.")

st.divider()


# ========================= SECTION 5: CHANGE HISTORY =========================

st.subheader("Change History")

audit_log = api_get("/settings/audit-log?limit=50")

if audit_log:
    df_data = []
    for entry in audit_log:
        df_data.append({
            "Timestamp": entry["changed_at"],
            "Table": entry["table_name"],
            "Record": entry["record_id"],
            "Field": entry["field_name"],
            "Old Value": entry.get("old_value") or "",
            "New Value": entry.get("new_value") or "",
            "Changed By": entry.get("changed_by_username") or "Unknown"
        })
    st.dataframe(pd.DataFrame(df_data), use_container_width=True, hide_index=True)
else:
    st.info("No changes have been recorded yet.")
