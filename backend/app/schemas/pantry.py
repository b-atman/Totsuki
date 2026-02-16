"""
Pydantic schemas for Pantry API endpoints.

These schemas define the API contracts:
- What data the API accepts (Create, Update)
- What data the API returns (Response)
- Validation rules for each field
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.pantry import ItemCategory, ItemSource


# =============================================================================
# Base Schema (shared fields)
# =============================================================================

class PantryItemBase(BaseModel):
    """
    Base schema with common fields for pantry items.
    Other schemas inherit from this to avoid repetition.
    """
    name: str = Field(
        ...,  # Required field
        min_length=1,
        max_length=255,
        description="Name of the item",
        examples=["Whole Milk", "Chicken Breast", "Olive Oil"]
    )
    canonical_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Normalized name for matching (auto-generated if not provided)",
        examples=["milk", "chicken", "oil"]
    )
    quantity: float = Field(
        default=1.0,
        gt=0,  # Must be greater than 0
        description="Amount of the item",
        examples=[1.0, 2.5, 0.5]
    )
    unit: str = Field(
        default="unit",
        max_length=50,
        description="Unit of measurement",
        examples=["unit", "lb", "oz", "cups", "gallon"]
    )
    estimated_expiry: Optional[datetime] = Field(
        default=None,
        description="Expected expiration date (ISO 8601 format)",
        examples=["2025-03-15T00:00:00Z"]
    )
    category: ItemCategory = Field(
        default=ItemCategory.OTHER,
        description="Grocery category for organization"
    )
    
    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        """Ensure name isn't just whitespace."""
        if not v.strip():
            raise ValueError("Name cannot be blank or whitespace only")
        return v.strip()
    
    @field_validator("unit")
    @classmethod
    def unit_must_not_be_blank(cls, v: str) -> str:
        """Ensure unit isn't just whitespace."""
        if not v.strip():
            return "unit"  # Default if blank
        return v.strip().lower()


# =============================================================================
# Create Schema (POST request body)
# =============================================================================

class PantryItemCreate(PantryItemBase):
    """
    Schema for creating a new pantry item.
    
    Inherits all fields from PantryItemBase.
    Source defaults to 'manual' for user-created items.
    """
    source: ItemSource = Field(
        default=ItemSource.MANUAL,
        description="How the item was added"
    )


# =============================================================================
# Update Schema (PUT request body)
# =============================================================================

class PantryItemUpdate(BaseModel):
    """
    Schema for updating an existing pantry item.
    
    All fields are optional - only provided fields are updated.
    This enables partial updates (PATCH-like behavior with PUT).
    """
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255
    )
    canonical_name: Optional[str] = Field(default=None, max_length=255)
    quantity: Optional[float] = Field(default=None, gt=0)
    unit: Optional[str] = Field(default=None, max_length=50)
    estimated_expiry: Optional[datetime] = None
    category: Optional[ItemCategory] = None
    
    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Name cannot be blank or whitespace only")
        return v.strip() if v else v


# =============================================================================
# Consume Schema (POST /inventory/consume)
# =============================================================================

class PantryItemConsume(BaseModel):
    """
    Schema for consuming (using) a pantry item.
    
    Reduces quantity by the specified amount.
    If quantity reaches 0, the item is deleted.
    """
    item_id: int = Field(
        ...,
        gt=0,
        description="ID of the item to consume"
    )
    quantity: float = Field(
        ...,
        gt=0,
        description="Amount to consume",
        examples=[1.0, 0.5]
    )


# =============================================================================
# Response Schema (API output)
# =============================================================================

class PantryItemResponse(PantryItemBase):
    """
    Schema for pantry item API responses.
    
    Includes all base fields plus database-generated fields
    like id, user_id, timestamps, and source.
    """
    id: int
    user_id: int
    source: ItemSource
    created_at: datetime
    last_updated: datetime
    
    # Allow ORM model instances to be converted to this schema
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# List Response (for GET /inventory)
# =============================================================================

class PantryListResponse(BaseModel):
    """
    Schema for listing pantry items with metadata.
    
    Includes pagination info and total count for frontend use.
    """
    items: list[PantryItemResponse]
    total: int = Field(description="Total number of items")
    
    model_config = ConfigDict(from_attributes=True)
