# This file defines Pydantic schemas that determine the shape of data for API
# requests and responses. They provide data validation, serialization, and
# documentation for the API endpoints.
from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


# ============================= CORE API SCHEMAS =============================

class Material(BaseModel):
    """
    Schema for representing a material in API responses.
    """
    id: int
    name: str
    description: Optional[str] = None
    cost_per_unit: Decimal
    min_cost_per_unit: Optional[Decimal] = None
    max_cost_per_unit: Optional[Decimal] = None
    cost_unit: Optional[str] = None
    currency: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LabourRate(BaseModel):
    """
    Schema for representing a labour rate in API responses.
    """
    id: int
    rate_name: str
    rate_per_hour: Decimal
    productivity_kg_per_day: Optional[Decimal] = None
    currency: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GlobalSetting(BaseModel):
    """
    Schema for representing a global setting in API responses.
    """
    setting_name: str
    setting_value: str

    model_config = ConfigDict(from_attributes=True)


class Component(BaseModel):
    """
    Schema for representing a component in API responses.

    This schema is used for reading component data and ensures that the
    response from endpoints like `/components/{component_id}` is correctly typed.
    """
    id: int  # The unique identifier for the component.
    name: str  # The human-readable name of the component.
    code: str  # A unique code for identifying the component.
    order_by: Optional[str] = None  # A field to specify the sorting order for display purposes.

    # This tells Pydantic to read data from ORM model attributes.
    model_config = ConfigDict(from_attributes=True)


class MotorWithLatestPrice(BaseModel):
    """
    Schema for representing a motor with its most recent price information.
    This is a flattened structure, ideal for API responses.
    """
    id: int
    supplier_name: str
    product_range: str
    part_number: Optional[str] = None
    poles: int
    rated_output: float  # Pydantic handles conversion from Decimal
    rated_output_unit: Optional[str] = None
    speed: int
    speed_unit: Optional[str] = None
    frame_size: Optional[str] = None
    shaft_diameter: Optional[float] = None
    shaft_diameter_unit: Optional[str] = None

    # Fields from the latest price record
    latest_price_date: Optional[date] = None
    foot_price: Optional[float] = None
    flange_price: Optional[float] = None
    currency: Optional[str] = None

    # Enable ORM mode to allow creating this schema from model instances
    model_config = ConfigDict(from_attributes=True)


class FanConfiguration(BaseModel):
    """
    Schema for representing a fan configuration in API responses.

    Used for reading fan configuration data from the database and returning it
    through the API.
    """
    id: int
    uid: str
    fan_size_mm: int
    hub_size_mm: int
    available_blade_qtys: List[int]
    stator_blade_qty: int
    blade_name: Optional[str] = None
    blade_material: Optional[str] = None
    mass_per_blade_kg: float  # Pydantic handles conversion from Decimal
    available_motor_kw: List[int]
    motor_pole: int
    available_components: Optional[List[int]] = None
    auto_selected_components: Optional[List[int]] = None

    # This tells Pydantic to read data from ORM model attributes.
    model_config = ConfigDict(from_attributes=True)


# ======================= SCHEMAS FOR QUOTE CALCULATION ======================

class ComponentQuoteRequest(BaseModel):
    """
    Defines the structure for a single component within a quote request.
    Includes the component's ID and any user-defined overrides.
    """
    component_id: int
    # Optional overrides for calculation parameters
    thickness_mm_override: Optional[float] = None
    fabrication_waste_factor_override: Optional[float] = None
    # Add other potential overrides here as the calculation engine evolves.


class QuoteRequest(BaseModel):
    """
    Defines the structure for an incoming quote calculation request.
    This is the main input to the calculation engine endpoint.
    """
    fan_configuration_id: int
    blade_quantity: int
    components: List[ComponentQuoteRequest]
    markup_override: Optional[float] = None
    motor_markup_override: Optional[float] = None
    motor_id: Optional[int] = None
    motor_mount_type: Optional[str] = None


class CalculatedComponent(BaseModel):
    """
    Represents the detailed calculated values for a single component in the response.
    This includes geometry, mass, costs, and the parameters used for the calculation.
    """
    # Identity
    name: str

    # Input Parameters (including overrides)
    material_thickness_mm: float
    fabrication_waste_percentage: float

    # Calculated Geometry
    overall_diameter_mm: Optional[float] = None # May not apply to all components
    total_length_mm: Optional[float] = None # May not apply to all components

    # Calculated Mass
    ideal_mass_kg: float
    real_mass_kg: float
    feedstock_mass_kg: float

    # Calculated Costs
    material_cost: float
    labour_cost: float
    total_cost_before_markup: float
    total_cost_after_markup: float

    # Other Factors
    stiffening_factor: Optional[float] = None # May not apply to all components

class ComponentCalculationRequest(BaseModel):
    """
    Defines the structure for a single component calculation request.
    This will be the input for our new endpoint.
    """
    fan_configuration_id: int
    component_id: int
    blade_quantity: int # Required for the Rotor calculator
    
    # Optional user-defined overrides
    thickness_mm_override: Optional[float] = None
    fabrication_waste_factor_override: Optional[float] = None
    markup_override: Optional[float] = None

class QuoteResponse(BaseModel):
    """
    Defines the structure of the final quote response returned by the API.
    """
    fan_uid: str
    total_mass_kg: float
    total_material_cost: float
    total_labour_cost: float
    subtotal_cost: float
    markup_applied: float
    final_price: float
    components: List[CalculatedComponent]
    motor_base_price: Optional[float] = None
    motor_markup_applied: Optional[float] = None
    motor_final_price: Optional[float] = None
    motor_details: Optional[dict] = None
