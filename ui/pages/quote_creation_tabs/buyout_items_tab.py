import streamlit as st
from config import CURRENCY_SYMBOL
from common import _new_quote_data, NEW_SCHEMA_VERSION

def render_main_content():
    st.header("4. Buy-out Items / Additional Costs")

    # Ensure quote_data present
    if "quote_data" not in st.session_state or not isinstance(st.session_state.quote_data, dict):
        st.session_state.quote_data = _new_quote_data()
    
    qd = st.session_state.quote_data
    spec_section = qd.setdefault("specification", {})
    
    # Buy-out items in specification section
    buy_list = spec_section.setdefault("buyouts", [])

    st.subheader("Add New Buy-out Item")
    with st.form("new_buyout_item_form", clear_on_submit=True):
        new_desc = st.text_input("Description", key="bo_new_desc")
        cols_buyout = st.columns(2)
        with cols_buyout[0]:
            new_cost = st.number_input(f"Unit Cost ({CURRENCY_SYMBOL})", min_value=0.0, step=10.0, format="%.2f", key="bo_new_cost")
        with cols_buyout[1]:
            new_qty = st.number_input("Quantity", min_value=1, step=1, value=1, key="bo_new_qty")
        add_item_submitted = st.form_submit_button("Add Item")

        if add_item_submitted and new_desc:
            item_id = f"item_{len(buy_list)}_{new_desc[:5]}"  # Simple unique ID
            new_item = {
                "id": item_id,
                "description": new_desc,
                "unit_cost": new_cost,
                "qty": new_qty,
                "subtotal": new_cost * new_qty,
            }
            buy_list.append(new_item)
            st.success(f"Added: {new_desc}")

    st.divider()
    st.subheader("Current Buy-out Items")
    if not buy_list:
        st.info("No buy-out items added yet.")
    else:
        total_buyout_cost = 0.0
        for i, item in enumerate(buy_list):
            # Recompute subtotal defensively in case of manual edits later
            item["subtotal"] = float(item.get("unit_cost", 0.0)) * float(item.get("qty", 0))
            total_buyout_cost += item["subtotal"]
            cols_item = st.columns([3, 1, 1, 1, 0.5])  # Description, Cost, Qty, Total, Remove
            with cols_item[0]:
                st.write(item.get('description',''))
            with cols_item[1]:
                st.write(f"{CURRENCY_SYMBOL} {item.get('unit_cost',0):.2f}")
            with cols_item[2]:
                st.write(f"{item.get('qty',0)}")
            with cols_item[3]:
                st.write(f"{CURRENCY_SYMBOL} {item.get('subtotal',0):.2f}")
            with cols_item[4]:
                if st.button("✖️", key=f"remove_bo_{item['id']}", help="Remove item"):
                    buy_list.pop(i)
                    st.rerun()
            if i < len(buy_list) - 1:
                st.markdown("---")  # lite divider

        st.divider()
        st.metric("Total Buy-out Items Cost", f"{CURRENCY_SYMBOL} {total_buyout_cost:,.2f}")