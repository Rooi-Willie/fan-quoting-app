import streamlit as st
from config import MOTOR_TYPES # Import motor types from config

def _update_quote_data_top_level_key(qd_top_level_key, widget_sstate_key):
    """
    Callback to update a key in st.session_state.quote_data
    from a widget's state in st.session_state.
    """
    if widget_sstate_key in st.session_state:
        st.session_state.quote_data[qd_top_level_key] = st.session_state[widget_sstate_key]

def render_main_content():
    st.header("2. Motor Selection")
    qd = st.session_state.quote_data

    cols = st.columns(2)
    with cols[0]:
        st.selectbox(
            "Motor Type",
            options=MOTOR_TYPES,
            index=MOTOR_TYPES.index(qd.get("motor_type", MOTOR_TYPES[0])),
            key="widget_motor_type_select",
            on_change=_update_quote_data_top_level_key,
            args=("motor_type", "widget_motor_type_select")
        )
        st.number_input(
            "Motor Power (kW)",
            min_value=0.1,
            step=0.1,
            value=float(qd.get("motor_power_kw", 11.0)),
            format="%.2f",
            key="widget_motor_power",
            on_change=_update_quote_data_top_level_key,
            args=("motor_power_kw", "widget_motor_power")
        )
    with cols[1]:
        voltage_options = ["230V", "400V", "415V", "525V", "Other"]
        st.selectbox(
            "Voltage (V)",
            options=voltage_options,
            index=voltage_options.index(qd.get("motor_voltage", "400V")),
            key="widget_motor_volt",
            on_change=_update_quote_data_top_level_key,
            args=("motor_voltage", "widget_motor_volt")
        )
        frequency_options = ["50Hz", "60Hz"]
        st.selectbox(
            "Frequency (Hz)",
            options=frequency_options,
            index=frequency_options.index(qd.get("motor_frequency", "50Hz")),
            key="widget_motor_freq",
            on_change=_update_quote_data_top_level_key,
            args=("motor_frequency", "widget_motor_freq")
        )

    st.text_area("Motor Specific Notes or Requirements",
                 value=qd.get("motor_notes", ""),
                 key="widget_motor_notes_area", height=100,
                 on_change=_update_quote_data_top_level_key,
                 args=("motor_notes", "widget_motor_notes_area"))