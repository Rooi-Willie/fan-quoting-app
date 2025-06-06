# fan_data.py
from typing import List, Dict
from .models import FanConfiguration # Import your Pydantic model

# Hardcoded data using Pydantic models
# This is loaded once when the application starts.
FAN_CONFIGS: List[FanConfiguration] = [
    FanConfiguration(
        pole="2 Pole",
        fan_size_mm=762,
        hub_size_mm=472,
        fan_id="Ø762-Ø472",
        different_blade_qty=[8, 10, 12],
        stator_blade_qty=13,
        blade_name_and_material="Yellow-Steel-As cast",
        motor_kw_range=[22, 30, 37, 45],
    ),
    FanConfiguration(
        pole="2 Pole",
        fan_size_mm=915,
        hub_size_mm=625,
        fan_id="Ø915-Ø625",
        different_blade_qty=[8, 10, 12],
        stator_blade_qty=13,
        blade_name_and_material="Yellow-Steel-As cast",
        motor_kw_range=[45, 55, 75],
    ),
    FanConfiguration(
        pole="2 Pole",
        fan_size_mm=1016,
        hub_size_mm=625,
        fan_id="Ø1016-Ø625",
        different_blade_qty=[6, 8, 10],
        stator_blade_qty=11,
        blade_name_and_material="Green- Steel-As cast",
        motor_kw_range=[45, 55, 75],
    ),
    FanConfiguration(
        pole="4 Pole",
        fan_size_mm=1200,
        hub_size_mm=685,
        fan_id="Ø1200-Ø685",
        different_blade_qty=[6, 10, 14],
        stator_blade_qty=15,
        blade_name_and_material="Orange-Ali-Trimmed",
        motor_kw_range=[55, 75, 90, 110],
    ),
    # IMPORTANT: I'm omitting the incomplete 'Ø1400-Ø?' and 'Ø1600-Ø?' entries
    # because they lack crucial information. If you want to include them,
    # you would need to make fields Optional as shown in models.py comments.
]

# For faster lookups by fan_id, create a dictionary from the list once at startup.
# This avoids iterating through the list every time a fan_id is requested.
FAN_ID_MAP: Dict[str, FanConfiguration] = {config.fan_id: config for config in FAN_CONFIGS}