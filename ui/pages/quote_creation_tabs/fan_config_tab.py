import streamlit as st
import os
import pandas as pd # Keep for potential future use, though not strictly needed if not building DF here
from config import COMPONENT_ORDER, COMPONENT_IMAGES, ROW_DEFINITIONS, IMAGE_FOLDER_PATH

def display_tab():
    st.header("3. Fan Configuration Details")
    qd = st.session_state.quote_data # Shorthand for quote_data
    cd = qd.setdefault("component_details", {}) # Shorthand for component_details, ensuring it exists

    # --- Base Fan Parameters ---
    st.subheader("Base Fan Parameters")
    cols_base = st.columns(3)
    with cols_base[0]:
        fan_id_options = [570, 620, 762, 915, 1016, 1200, 1400, 1600]
        qd["fan_id"] = st.selectbox(
            "Fan ID (mm)", options=fan_id_options,
            index=fan_id_options.index(qd.get("fan_id", 570)),
            key="fc_fan_id"
        )
    with cols_base[1]:
        fan_hub_options = [400, 472, 625, 685, 914, 850]
        qd["fan_hub"] = st.selectbox(
            "Fan Hub (mm)", options=fan_hub_options,
            index=fan_hub_options.index(qd.get("fan_hub", 400)),
            key="fc_fan_hub"
        )
    with cols_base[2]:
        qd["blade_sets"] = st.number_input(
            "Blade Sets", min_value=1, step=1,
            value=int(qd.get("blade_sets", 1)),
            key="fc_blade_sets"
        )
    st.divider()

    # --- Component Selection ---
    st.subheader("Fan Components Selection & Configuration")
    qd["selected_components_unordered"] = st.multiselect(
        "Select Fan Components (order will be fixed below)",
        options=COMPONENT_ORDER,
        default=qd.get("selected_components_unordered", []),
        key="fc_multiselect_components"
    )

    # Derive the ordered list for processing
    ordered_selected_components = [
        comp for comp in COMPONENT_ORDER if comp in qd.get("selected_components_unordered", [])
    ]

    if not ordered_selected_components:
        st.info("Select fan components above to configure them.")
        # Clean up details for components that are no longer selected
        keys_to_remove = [k for k in cd if k not in ordered_selected_components]
        for k_rem in keys_to_remove:
            del cd[k_rem]
        return

    num_selected_components = len(ordered_selected_components)
    column_layout_config = [1.5] + [1] * num_selected_components # Label col + component cols

    # --- Component Image Row ---
    image_cols = st.columns(column_layout_config)
    with image_cols[0]: st.markdown("**Image**")
    for i, comp_name in enumerate(ordered_selected_components):
        with image_cols[i + 1]:
            image_full_path = COMPONENT_IMAGES.get(comp_name)
            if image_full_path and os.path.exists(image_full_path):
                st.image(image_full_path, use_column_width='always', caption=comp_name[:15]+"...") # Keep caption short
            elif image_full_path: # Path defined but file missing
                st.warning(f"Img missing: {os.path.basename(image_full_path)}")
            else: # Path not configured
                st.markdown("*(No Image)*")

    # --- Header Row for Parameters ---
    header_cols = st.columns(column_layout_config)
    with header_cols[0]: st.markdown("**Parameter**")
    for i, comp_name in enumerate(ordered_selected_components):
        with header_cols[i + 1]: st.markdown(f"**{comp_name}**")
    st.divider()

    # --- Data Input/Display Area ---
    for row_idx, (row_label, row_type, default_val, unit_or_curr) in enumerate(ROW_DEFINITIONS):
        param_row_cols = st.columns(column_layout_config)
        with param_row_cols[0]:
            display_label = f"{row_label} ({unit_or_curr})" if unit_or_curr not in ["factor", "%"] else row_label
            st.markdown(display_label)
            if unit_or_curr in ["factor", "%"]:
                 st.caption(f"Unit: {unit_or_curr}")


        for comp_idx, comp_name in enumerate(ordered_selected_components):
            cd.setdefault(comp_name, {}) # Ensure component dict exists in component_details
            widget_key_unique = f"fc_{comp_name}_{row_label.replace(' ', '_')}_{row_idx}_{comp_idx}"

            with param_row_cols[comp_idx + 1]:
                current_value_for_display = cd[comp_name].get(row_label, default_val)

                if row_type == 'DB':
                    # For demo, vary DB values slightly. In real app, fetch from DB/rules engine
                    # based on fan_id, comp_name etc.
                    # This value should ideally be calculated/fetched once and stored if it's complex
                    # For simplicity, using a placeholder:
                    db_value_to_display = default_val * (1 + comp_idx * 0.02) # Example variation
                    st.text(f"{db_value_to_display:.2f}")
                    cd[comp_name][row_label] = db_value_to_display # Store the displayed value
                elif row_type == 'Calc':
                    # Placeholder: Actual calculation should happen here or be triggered
                    # For now, just use a dummy value variation
                    # This calculation would use other values from cd[comp_name] or qd
                    calc_value_to_display = default_val * (1 - comp_idx * 0.01) # Example variation
                    st.text(f"{calc_value_to_display:.2f}")
                    cd[comp_name][row_label] = calc_value_to_display # Store the displayed value
                elif row_type == 'Mod':
                    step_val = 0.1
                    fmt_str = "%.2f"
                    if unit_or_curr == '%':
                        step_val = 1.0
                        fmt_str = "%.1f"
                    elif unit_or_curr == "mm":
                        step_val = 0.5
                        fmt_str = "%.1f"
                    elif unit_or_curr == "factor":
                        step_val = 0.01
                    elif unit_or_curr == "hrs":
                        step_val = 0.5
                        fmt_str = "%.1f"

                    user_value = st.number_input(
                        label=f"_{row_label}_{comp_name}", # Underscore for hidden label
                        label_visibility="collapsed",
                        value=float(current_value_for_display), # Ensure float for number_input
                        step=step_val,
                        format=fmt_str,
                        key=widget_key_unique,
                    )
                    cd[comp_name][row_label] = user_value # Update session state
    # Clean up details for components that are no longer selected (important!)
    keys_to_remove = [k for k in cd if k not in ordered_selected_components]
    for k_rem in keys_to_remove:
        del cd[k_rem]