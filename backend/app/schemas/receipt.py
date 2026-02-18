"""
Pydantic schemas for Receipt Ingestion API.

These schemas define the API contracts for:
- CSV upload and parsing
- Receipt item storage
- Spend analytics
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.pantry import ItemCategory


# =============================================================================
# Receipt Item Schemas
# =============================================================================

class ReceiptItemBase(BaseModel):
    """Base schema for receipt item fields."""
    raw_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Original item name from receipt"
    )
    quantity: float = Field(
        default=1.0,
        gt=0,
        description="Quantity purchased"
    )
    unit: str = Field(
        default="unit",
        max_length=50,
        description="Unit of measurement"
    )
    unit_price: float = Field(
        ...,
        ge=0,
        description="Price per unit"
    )
    category: ItemCategory = Field(
        default=ItemCategory.OTHER,
        description="Item category"
    )


class ReceiptItemCreate(ReceiptItemBase):
    """
    Schema for creating a receipt item during CSV ingestion.
    
    The normalized_name and total_price are computed by the service layer.
    """
    pass


class ReceiptItemResponse(ReceiptItemBase):
    """Full receipt item response with all computed and DB fields."""
    id: int
    user_id: int
    receipt_batch_id: str
    normalized_name: str
    total_price: float
    store: str
    purchase_date: datetime
    matched_pantry_item_id: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ReceiptItemPreview(BaseModel):
    """
    Preview of a parsed receipt item before confirmation.
    
    Shows what will be created/updated, including pantry match info.
    """
    raw_name: str
    normalized_name: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    category: ItemCategory
    
    # Pantry matching info
    pantry_match_name: Optional[str] = Field(
        default=None,
        description="Name of matched pantry item (if any)"
    )
    pantry_match_id: Optional[int] = Field(
        default=None,
        description="ID of matched pantry item (if any)"
    )
    match_score: Optional[float] = Field(
        default=None,
        description="Confidence score of pantry match (0-1)"
    )
    will_create_new: bool = Field(
        default=False,
        description="True if this will create a new pantry item"
    )


# =============================================================================
# CSV Upload Schemas
# =============================================================================

class CSVUploadRequest(BaseModel):
    """
    Metadata for CSV receipt upload.
    
    The actual CSV file is sent as multipart form data.
    This schema validates the accompanying metadata.
    """
    store: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Store name (e.g., 'Walmart', 'Kroger')",
        examples=["Walmart", "Kroger", "Costco"]
    )
    purchase_date: datetime = Field(
        ...,
        description="Date of purchase (ISO 8601 format)",
        examples=["2026-02-18T00:00:00Z"]
    )
    
    @field_validator("store")
    @classmethod
    def store_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Store name cannot be blank")
        return v.strip()


class CSVParseResponse(BaseModel):
    """
    Response from parsing a CSV file (before confirmation).
    
    Returns preview items for user review before committing.
    """
    batch_id: str = Field(description="Unique ID for this upload batch")
    store: str
    purchase_date: datetime
    items: list[ReceiptItemPreview]
    total_items: int
    total_amount: float = Field(description="Sum of all item totals")
    matched_count: int = Field(description="Items matched to existing pantry")
    new_count: int = Field(description="Items that will create new pantry entries")


class ReceiptConfirmRequest(BaseModel):
    """
    Request to confirm and commit a parsed receipt.
    
    Allows user to modify items before final commit.
    """
    batch_id: str = Field(description="Batch ID from parse response")
    store: str
    purchase_date: datetime
    items: list[ReceiptItemCreate]
    update_pantry: bool = Field(
        default=True,
        description="Whether to update pantry quantities"
    )


class ReceiptIngestionResponse(BaseModel):
    """Response after successfully ingesting a receipt."""
    batch_id: str
    items_created: int
    pantry_items_updated: int
    pantry_items_created: int
    total_amount: float
    message: str


# =============================================================================
# Analytics Schemas
# =============================================================================

class SpendByCategory(BaseModel):
    """Spending breakdown for a single category."""
    category: str
    total_spent: float
    item_count: int
    percentage: float = Field(description="Percentage of total spending")


class SpendByStore(BaseModel):
    """Spending breakdown for a single store."""
    store: str
    total_spent: float
    visit_count: int = Field(description="Number of receipts from this store")
    percentage: float


class SpendByMonth(BaseModel):
    """Spending for a single month."""
    month: str = Field(description="Month in YYYY-MM format")
    total_spent: float
    item_count: int


class SpendBreakdownResponse(BaseModel):
    """
    Complete spending analytics response.
    
    Provides breakdowns by category, store, and time for charts.
    """
    # Summary
    total_spent: float
    total_items: int
    total_receipts: int
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    
    # Breakdowns for charts
    by_category: list[SpendByCategory]
    by_store: list[SpendByStore]
    by_month: list[SpendByMonth]
    
    # Top items by spending
    top_items: list[dict] = Field(
        default_factory=list,
        description="Top items by total spending"
    )
