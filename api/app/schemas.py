# This file defines the data shapes for API requests and responses, providing validation.

from pydantic import BaseModel, ConfigDict
from typing import List

# Pydantic schema for the Component model
class Component(BaseModel):
    id: int
    name: str
    code: str
    order_by: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Pydantic schema for the FanConfiguration model
class FanConfiguration(BaseModel):
    id: int
    uid: str
    fan_size_mm: int
    hub_size_mm: int
    available_blade_qtys: List[int]
    available_motor_kw: List[int]
    available_components: List[int] | None = None
    auto_selected_components: List[int] | None = None

    # This tells Pydantic to read data even if it's not a dict (e.g., from ORM models)
    model_config = ConfigDict(from_attributes=True)