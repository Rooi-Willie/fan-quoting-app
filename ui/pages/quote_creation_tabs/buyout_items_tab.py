import streamlit as st
from config import CURRENCY_SYMBOL
def render_main_content():
    st.header("4. Buy-out Items / Additional Costs")
    qd = st.session_state.quote_data
    # Ensure 'buy_out_items_list' exists and is a list
    if "buy_out_items_list" not in qd or not isinstance(qd["buy_out_items_list"], list):
        qd["buy_out_items_list"] = []

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
            qd["buy_out_items_list"].append({
                "id": f"item_{len(qd['buy_out_items_list'])}_{new_desc[:5]}", # Simple unique ID
                "description": new_desc,
                "cost": new_cost,
                "quantity": new_qty
            })
            st.success(f"Added: {new_desc}")

    st.divider()
    st.subheader("Current Buy-out Items")
    if not qd["buy_out_items_list"]:
        st.info("No buy-out items added yet.")
    else:
        total_buyout_cost = 0
        for i, item in enumerate(qd["buy_out_items_list"]):
            item_total = item['cost'] * item['quantity']
            total_buyout_cost += item_total
            cols_item = st.columns([3, 1, 1, 1, 0.5]) # Description, Cost, Qty, Total, Remove
            with cols_item[0]:
                st.write(item['description'])
            with cols_item[1]:
                st.write(f"{CURRENCY_SYMBOL} {item['cost']:.2f}")
            with cols_item[2]:
                st.write(f"{item['quantity']}")
            with cols_item[3]:
                st.write(f"{CURRENCY_SYMBOL} {item_total:.2f}")
            with cols_item[4]:
                if st.button("✖️", key=f"remove_bo_{item['id']}", help="Remove item"):
                    qd["buy_out_items_list"].pop(i)
                    st.rerun() # Rerun to reflect removal
            if i < len(qd["buy_out_items_list"]) -1 : st.markdown("---") # lite divider

        st.divider()
        st.metric("Total Buy-out Items Cost", f"{CURRENCY_SYMBOL} {total_buyout_cost:,.2f}")