# models.py
from pydantic import BaseModel, Field, ValidationError
from typing import List, Literal, Optional, Dict

class FanConfiguration(BaseModel):
    """
    Represents a single fan configuration entry from the table.
    """
    pole: Literal["2 Pole", "4 Pole"] = Field(..., description="Motor pole configuration (e.g., '2 Pole', '4 Pole').")

    # --- Addressing your Question 1 (Fan size/Hub size) ---
    # It's better to store diameter as integers for calculations.
    # fan_id can remain a string for display and lookup, or be a computed property.
    fan_size_mm: int = Field(..., description="Fan size diameter in mm (e.g., 762).")
    hub_size_mm: int = Field(..., description="Hub size diameter in mm (e.g., 472).")

    # Optional: Keep fan_id as a separate field if you prefer it as a direct lookup key
    # and it might deviate from the auto-generated format.
    # If it's always Ø<fan_size>-Ø<hub_size>, you can make it a @property.
    fan_id: str = Field(..., description="Combined display ID for Fan size-Hub size (e.g., 'Ø762-Ø472'). This is the unique identifier for lookup.")

    # Alternative: If fan_id is *always* derived, make it a @property
    # @property
    # def fan_id(self) -> str:
    #    return f"Ø{self.fan_size_mm}-Ø{self.hub_size_mm}"
    # In this case, you wouldn't include `fan_id: str` in the BaseModel,
    # and you would need to adjust how you construct the initial data.
    # For now, let's keep it explicit as a field for simpler data instantiation.


    different_blade_qty: List[int] = Field(..., description="List of possible quantities for different blades (e.g., [8, 10, 12]).")
    stator_blade_qty: int = Field(..., description="Quantity of stator blades.")
    blade_name_and_material: str = Field(..., description="Name and material of the blade (e.g., 'Yellow-Steel-As cast').")
    motor_kw_range: List[int] = Field(..., description="List of motor kW ranges (e.g., [22, 30, 37, 45]).")

    # --- Handling incomplete data ---
    # For entries like Ø1400-Ø?, you can use Optional and provide None or empty defaults.
    # Pydantic will allow these fields to be missing or None if marked Optional.
    # Example for an incomplete entry if you were to store it:
    # fan_size_mm: Optional[int] = None
    # hub_size_mm: Optional[int] = None
    # different_blade_qty: Optional[List[int]] = None # or Field(default_factory=list) for empty list
    # stator_blade_qty: Optional[int] = None
    # blade_name_and_material: Optional[str] = None
    # motor_kw_range: Optional[List[int]] = None # or Field(default_factory=list)