# This file defines Pydantic schemas that determine the shape of data for API
# requests and responses. They provide data validation, serialization, and
# documentation for the API endpoints.
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum
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
    total_quote_price: float
    components: List[CalculatedComponent]
    motor_base_price: Optional[float] = None
    motor_markup_applied: Optional[float] = None
    motor_final_price: Optional[float] = None
    motor_details: Optional[dict] = None

# ============= SCHEMAS FOR SAVING AND MANAGING QUOTES ==============
class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent" 
    APPROVED = "approved"
    REJECTED = "rejected"

class UserBase(BaseModel):
    email: str
    name: Optional[str] = None
    role: Optional[str] = "user"

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class QuoteBase(BaseModel):
    quote_ref: str
    client_name: Optional[str] = None
    project_name: Optional[str] = None
    project_location: Optional[str] = None
    status: Optional[QuoteStatus] = QuoteStatus.DRAFT

class QuoteCreate(QuoteBase):
    quote_data: Dict[str, Any]
    user_id: int

class QuoteUpdate(BaseModel):
    client_name: Optional[str] = None
    project_name: Optional[str] = None
    project_location: Optional[str] = None
    status: Optional[QuoteStatus] = None
    quote_data: Optional[Dict[str, Any]] = None

class QuoteRevision(BaseModel):
    original_quote_id: int

class QuoteSummary(QuoteBase):
    id: int
    revision_number: int
    creation_date: datetime
    # Summary fields below are SERVER-DERIVED from quote_data nested schema.
    # They are retained for fast listing queries. Client should not rely on
    # sending these in create/update requests. (See crud._extract_summary_from_quote_data)
    fan_uid: Optional[str] = None
    fan_size_mm: Optional[int] = None
    blade_sets: Optional[int] = None
    component_list: Optional[List[str]] = None
    markup: Optional[float] = None
    motor_supplier: Optional[str] = None
    motor_rated_output: Optional[str] = None
    total_price: Optional[float] = None
    
    class Config:
        orm_mode = True

class Quote(QuoteSummary):
    quote_data: Dict[str, Any]
    original_quote_id: Optional[int] = None
    
    class Config:
        orm_mode = True


# ======================= QUOTE DATA V3 SCHEMA MODELS ======================

class QuoteMetaV3(BaseModel):
    """Schema for quote metadata section in v3 format."""
    version: int = 3
    created_at: str
    updated_at: str
    created_by: str

class QuoteInfoV3(BaseModel):
    """Schema for quote information section in v3 format."""
    reference: str
    client: str
    project: str
    location: str
    notes: Optional[str] = ""

class FanSpecificationV3(BaseModel):
    """Schema for fan specification in v3 format."""
    config_id: int
    uid: str
    fan_size_mm: int
    hub_size_mm: int
    blade_sets: str

class MotorSpecificationV3(BaseModel):
    """Schema for motor specification in v3 format."""
    selection_id: int
    mount_type: str
    supplier_name: str
    rated_output: float
    poles: int

class BuyoutItemV3(BaseModel):
    """Schema for individual buyout item in v3 format."""
    description: str
    unit_cost: float
    qty: int
    notes: Optional[str] = ""

class SpecificationSectionV3(BaseModel):
    """Schema for specification section in v3 format."""
    fan: FanSpecificationV3
    motor: MotorSpecificationV3
    components: List[str]
    buyouts: List[BuyoutItemV3]

class ComponentOverrideV3(BaseModel):
    """Schema for component override parameters in v3 format."""
    thickness_mm: Optional[float] = None
    waste_pct: Optional[float] = None

class PricingSectionV3(BaseModel):
    """Schema for pricing section in v3 format."""
    component_markup: float
    motor_markup: float
    overrides: Dict[str, ComponentOverrideV3]

class ComponentCalculationV3(BaseModel):
    """Schema for individual component calculation in v3 format."""
    overall_diameter_mm: Optional[float] = None
    total_length_mm: Optional[float] = None
    stiffening_factor: Optional[float] = None
    ideal_mass_kg: float
    real_mass_kg: float
    feedstock_mass_kg: float
    material_cost: float
    labour_cost: float
    cost_before_markup: float
    cost_after_markup: float

class ComponentTotalsV3(BaseModel):
    """Schema for aggregated component totals in v3 format."""
    total_length_mm: float
    total_mass_kg: float
    total_labour_cost: float
    total_material_cost: float
    subtotal_cost: float
    final_price: float

class QuoteTotalsV3(BaseModel):
    """Schema for final quote totals in v3 format."""
    components: float
    motor: float
    buyouts: float
    grand_total: float

class CalculationsSectionV3(BaseModel):
    """Schema for calculations section in v3 format."""
    timestamp: str
    components: Dict[str, ComponentCalculationV3]
    component_totals: ComponentTotalsV3
    totals: QuoteTotalsV3

class ContextSectionV3(BaseModel):
    """Schema for context section in v3 format."""
    fan_configuration: Dict[str, Any]
    motor_details: Dict[str, Any]
    rates_and_settings: Dict[str, Any]

class QuoteDataV3(BaseModel):
    """Complete schema for quote data in v3 format."""
    meta: QuoteMetaV3
    quote: QuoteInfoV3
    specification: SpecificationSectionV3
    pricing: PricingSectionV3
    calculations: CalculationsSectionV3
    context: ContextSectionV3