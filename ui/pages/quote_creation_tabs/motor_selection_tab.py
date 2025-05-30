import streamlit as st
from config import MOTOR_TYPES # Import motor types from config

def display_tab():
    st.header("2. Motor Selection")
    qd = st.session_state.quote_data

    cols = st.columns(2)
    with cols[0]:
        qd["motor_type"] = st.selectbox(
            "Motor Type",
            options=MOTOR_TYPES,
            index=MOTOR_TYPES.index(qd.get("motor_type", MOTOR_TYPES[0])),
            key="motor_type_select"
        )
        qd["motor_power_kw"] = st.number_input(
            "Motor Power (kW)",
            min_value=0.1,
            step=0.1,
            value=float(qd.get("motor_power_kw", 11.0)),
            format="%.2f",
            key="motor_power"
        )
    with cols[1]:
        qd["motor_voltage"] = st.selectbox(
            "Voltage (V)",
            options=["230V", "400V", "415V", "525V", "Other"],
            index=["230V", "400V", "415V", "525V", "Other"].index(qd.get("motor_voltage", "400V")),
            key="motor_volt"
        )
        qd["motor_frequency"] = st.selectbox(
            "Frequency (Hz)",
            options=["50Hz", "60Hz"],
            index=["50Hz", "60Hz"].index(qd.get("motor_frequency", "50Hz")),
            key="motor_freq"
        )

    st.text_area("Motor Specific Notes or Requirements", value=qd.get("motor_notes", ""), key="motor_notes_area", height=100,
                 on_change=lambda: st.session_state.quote_data.update({"motor_notes": st.session_state.motor_notes_area}))