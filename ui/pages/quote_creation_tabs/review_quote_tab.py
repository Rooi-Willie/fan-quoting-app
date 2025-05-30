import streamlit as st
import pandas as pd
import numpy as np # For np.nan
from config import ROW_DEFINITIONS, CURRENCY_SYMBOL, COMPONENT_ORDER # For ordering if needed

def display_tab():
    st.header("5. Review & Finalize Quote")
    qd = st.session_state.quote_data
    cd = qd.get("component_details", {})

    # --- Display Basic Info ---
    st.subheader("Project & Motor Information")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Project Name:** {qd.get('project_name', 'N/A')}")
        st.markdown(f"**Client Name:** {qd.get('client_name', 'N/A')}")
        st.markdown(f"**Quote Reference:** {qd.get('quote_ref', 'N/A')}")
    with col2:
        st.markdown(f"**Motor Type:** {qd.get('motor_type', 'N/A')}")
        st.markdown(f"**Motor Power:** {qd.get('motor_power_kw', 0.0):.2f} kW")
        st.markdown(f"**Fan ID:** {qd.get('fan_id', 'N/A')} mm")

    st.divider()

    # --- Fan Component Summary Table ---
    st.subheader("Fan Component Cost & Mass Summary")
    if not cd or not any(cd.values()): # Check if component_details is empty or has no actual data
        st.info("No fan components configured yet. Please go to the 'Fan Configuration' tab.")
    else:
        # Filter cd to only include selected and ordered components
        ordered_selected_components_for_summary = [
            comp for comp in COMPONENT_ORDER if comp in qd.get("selected_components_unordered", []) and comp in cd
        ]
        filtered_cd_for_df = {comp: cd[comp] for comp in ordered_selected_components_for_summary if comp in cd}


        if not filtered_cd_for_df:
            st.info("No data for selected components. Please check 'Fan Configuration' tab.")
            return

        ordered_rows_labels = [row_tuple[0] for row_tuple in ROW_DEFINITIONS]
        try:
            # Create DataFrame from the filtered and ordered component details
            summary_df = pd.DataFrame(filtered_cd_for_df)
            # Reindex to ensure all defined rows are present and in order
            summary_df = summary_df.reindex(index=ordered_rows_labels)
        except Exception as e:
            st.error(f"Error creating summary DataFrame: {e}")
            st.json(filtered_cd_for_df) # Show data that caused the error
            return # Stop further processing for this section

        # Calculate 'Total' column
        rows_to_sum = ["Real Mass", "Feedstock Mass", f"Material Cost", "Labour", f"Total Cost"]
        valid_rows_to_sum = [r for r in rows_to_sum if r in summary_df.index]

        summary_df['Total'] = np.nan # Initialize with NaN for Arrow compatibility
        if valid_rows_to_sum and not summary_df.select_dtypes(include=np.number).empty:
            numeric_cols_for_sum = summary_df.columns[summary_df.columns != 'Total']
            summary_df.loc[valid_rows_to_sum, 'Total'] = summary_df.loc[valid_rows_to_sum, numeric_cols_for_sum].sum(axis=1, skipna=True)

        # --- Configure Column Formatting for st.dataframe ---
        st_col_config = {}
        row_format_details = {row[0]: (row[3], row[1]) for row in ROW_DEFINITIONS} # label: (unit, type)

        for df_col_name in summary_df.columns: # Iterate over DataFrame columns (Component names + 'Total')
            # Default formatting for the column - applied if no row-specific format matches
            st_col_config[df_col_name] = st.column_config.NumberColumn(
                label=str(df_col_name),
                format="%.2f" # Generic float
            )

        # Apply specific formatting to cells based on row_label's unit_hint
        # This is a bit tricky as st.column_config is column-wide.
        # We will format the DataFrame for display instead, then show it.
        # OR, we can create a new DF with formatted strings for st.dataframe if direct config is too limited.
        # For now, let's try to make NumberColumn work as much as possible.
        # The best is to have consistent types in columns. NaNs are fine.

        # Since st.column_config applies to the whole column, we create a styled DF for display
        styled_df = summary_df.copy().astype(object) # Copy to object to allow mixed types (strings for formatted numbers)

        for row_label_df, (unit, row_type) in row_format_details.items():
            if row_label_df not in styled_df.index: continue
            for col_name_df in styled_df.columns:
                val = styled_df.loc[row_label_df, col_name_df]
                if pd.isna(val):
                    styled_df.loc[row_label_df, col_name_df] = "---" # Display NaNs as "---"
                    continue

                try:
                    if unit == CURRENCY_SYMBOL:
                        styled_df.loc[row_label_df, col_name_df] = f"{CURRENCY_SYMBOL} {float(val):,.2f}"
                    elif unit == '%':
                        styled_df.loc[row_label_df, col_name_df] = f"{float(val):.1f} %"
                    elif unit == 'kg':
                        styled_df.loc[row_label_df, col_name_df] = f"{float(val):.2f} kg"
                    elif unit == 'mm':
                        styled_df.loc[row_label_df, col_name_df] = f"{float(val):.1f} mm"
                    elif unit == 'hrs':
                        styled_df.loc[row_label_df, col_name_df] = f"{float(val):.1f} hrs"
                    elif unit == 'factor':
                         styled_df.loc[row_label_df, col_name_df] = f"{float(val):.2f}"
                    # else keep as is, or add more specific formats
                except (ValueError, TypeError): # If value can't be converted to float (e.g. already "---")
                    pass # Keep the existing value

        st.dataframe(styled_df, use_container_width=True) # Display the manually formatted DataFrame

        # --- Grand Totals ---
        st.divider()
        st.subheader("Quote Grand Totals")

        fan_components_total_cost = 0.0
        if f"Total Cost" in summary_df.index and 'Total' in summary_df.columns and pd.notna(summary_df.loc[f"Total Cost", 'Total']):
            fan_components_total_cost = float(summary_df.loc[f"Total Cost", 'Total'])

        buy_out_total_cost = sum(item['cost'] * item['quantity'] for item in qd.get("buy_out_items_list", []))

        grand_total_quote = fan_components_total_cost + buy_out_total_cost

        summary_cols = st.columns(3)
        with summary_cols[0]:
            st.metric(f"Total Fan Components Cost", f"{CURRENCY_SYMBOL} {fan_components_total_cost:,.2f}")
        with summary_cols[1]:
            st.metric(f"Total Buy-out Items Cost", f"{CURRENCY_SYMBOL} {buy_out_total_cost:,.2f}")
        with summary_cols[2]:
            st.metric("GRAND TOTAL QUOTE", f"{CURRENCY_SYMBOL} {grand_total_quote:,.2f}", delta_color="off")

    st.divider()
    if st.button("🖨️ Generate Quote Document (Placeholder)", use_container_width=True):
        # Logic to generate PDF/Word document using collected data from st.session_state.quote_data
        # Libraries like FPDF, reportlab, python-docx could be used.
        st.success("Quote document generation logic would be triggered here!")
        st.balloons()