import streamlit as st
from config import CURRENCY_SYMBOL
from common import _new_quote_data, NEW_SCHEMA_VERSION
from utils import api_get


@st.cache_data(ttl=300)
def _fetch_buyout_catalog() -> list:
    """Fetch all active buyout catalog items from the API (cached 5 min)."""
    result = api_get("/buyout-catalog")
    return result if isinstance(result, list) else []


def render_main_content():
    st.header("4. Buy-out Items / Additional Costs")

    # Ensure quote_data present
    if "quote_data" not in st.session_state or not isinstance(st.session_state.quote_data, dict):
        st.session_state.quote_data = _new_quote_data()

    qd = st.session_state.quote_data

    from common import get_active_config
    active_cfg = get_active_config(qd)
    if not active_cfg:
        st.warning("No fan configuration available. Please add one from the sidebar.")
        return

    spec_section = active_cfg.setdefault("specification", {})

    # Dynamic widget key suffix for config-aware widget keys
    widget_reset_counter = st.session_state.get("widget_reset_counter", 0)
    widget_key_suffix = f"_{widget_reset_counter}"

    # Buy-out items in specification section
    buy_list = spec_section.setdefault("buyouts", [])

    # ------------------------------------------------------------------ #
    # SELECT FROM CATALOG                                                  #
    # ------------------------------------------------------------------ #
    with st.expander("Select from Catalog", expanded=False):
        catalog_items = _fetch_buyout_catalog()

        if not catalog_items:
            st.info("Catalog is unavailable. Use the manual form below.")
        else:
            # Distinct manufacturers
            manufacturers = sorted({item["manufacturer"] for item in catalog_items})
            selected_manufacturer = st.selectbox(
                "Manufacturer",
                options=manufacturers,
                key=f"bo_cat_manufacturer{widget_key_suffix}",
            )

            # Filter items by selected manufacturer
            mfr_items = [i for i in catalog_items if i["manufacturer"] == selected_manufacturer]

            # Voltage options — only show if catalog items for this manufacturer have voltages
            voltages = sorted({i["voltage_v"] for i in mfr_items if i.get("voltage_v") is not None})
            if voltages:
                voltage_labels = {v: f"{v} V AC" for v in voltages}
                selected_voltage = st.selectbox(
                    "Voltage",
                    options=voltages,
                    format_func=lambda v: voltage_labels[v],
                    key=f"bo_cat_voltage{widget_key_suffix}",
                )
                filtered_items = [i for i in mfr_items if i.get("voltage_v") == selected_voltage]
            else:
                selected_voltage = None
                filtered_items = mfr_items

            # Build display options
            def _item_label(item: dict) -> str:
                if item.get("is_por"):
                    return f"{item['description']}  —  Price on Request"
                price = item.get("unit_price")
                return f"{item['description']}  —  {CURRENCY_SYMBOL} {float(price):,.2f}"

            item_options = list(range(len(filtered_items)))
            selected_item_idx = st.selectbox(
                "Item",
                options=item_options,
                format_func=lambda idx: _item_label(filtered_items[idx]),
                key=f"bo_cat_item{widget_key_suffix}",
            )

            cat_qty = st.number_input(
                "Quantity",
                min_value=1,
                step=1,
                value=1,
                key=f"bo_cat_qty{widget_key_suffix}",
            )

            selected_item = filtered_items[selected_item_idx] if filtered_items else None
            is_por = selected_item and selected_item.get("is_por", False)

            if is_por:
                st.warning(
                    "This item is **Price on Request** — contact the supplier for a quote, "
                    "then add it manually using the form below."
                )

            add_from_catalog = st.button(
                "Add to Quote",
                key=f"bo_cat_add{widget_key_suffix}",
                disabled=(not selected_item or is_por),
            )

            if add_from_catalog and selected_item and not is_por:
                unit_cost = float(selected_item["unit_price"])
                item_id = f"item_{len(buy_list)}_{selected_item['description'][:5]}"
                new_item = {
                    "id": item_id,
                    "description": selected_item["description"],
                    "unit_cost": unit_cost,
                    "qty": int(cat_qty),
                    "subtotal": unit_cost * int(cat_qty),
                }
                buy_list.append(new_item)
                st.success(f"Added: {selected_item['description']}")
                st.rerun()

    st.divider()

    # ------------------------------------------------------------------ #
    # MANUAL ENTRY FORM                                                    #
    # ------------------------------------------------------------------ #
    st.subheader("Add New Buy-out Item")
    with st.form(f"new_buyout_item_form{widget_key_suffix}", clear_on_submit=True):
        new_desc = st.text_input("Description", key=f"bo_new_desc{widget_key_suffix}")
        cols_buyout = st.columns(2)
        with cols_buyout[0]:
            new_cost = st.number_input(f"Unit Cost ({CURRENCY_SYMBOL})", min_value=0.0, step=10.0, format="%.2f", key=f"bo_new_cost{widget_key_suffix}")
        with cols_buyout[1]:
            new_qty = st.number_input("Quantity", min_value=1, step=1, value=1, key=f"bo_new_qty{widget_key_suffix}")
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
                if st.button("✖️", key=f"remove_bo_{item['id']}{widget_key_suffix}", help="Remove item"):
                    buy_list.pop(i)
                    st.rerun()
            if i < len(buy_list) - 1:
                st.markdown("---")  # lite divider

        st.divider()
        st.metric("Total Buy-out Items Cost", f"{CURRENCY_SYMBOL} {total_buyout_cost:,.2f}")
