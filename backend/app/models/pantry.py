"""
PantryItem model - represents items in the user's pantry inventory.

This is the core data model for tracking what ingredients/items
a user has at home, including quantities, expiry dates, and categories.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Float, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ItemSource(str, Enum):
    """How the item was added to the pantry."""
    MANUAL = "manual"      # User added it manually
    RECEIPT = "receipt"    # Extracted from a receipt


class ItemCategory(str, Enum):
    """
    Standard grocery categories for organizing items.
    Helps with meal planning and shopping list grouping.
    """
    PRODUCE = "produce"
    DAIRY = "dairy"
    MEAT = "meat"
    SEAFOOD = "seafood"
    BAKERY = "bakery"
    FROZEN = "frozen"
    PANTRY = "pantry"          # Canned goods, dry goods, etc.
    BEVERAGES = "beverages"
    SNACKS = "snacks"
    CONDIMENTS = "condiments"
    SPICES = "spices"
    OTHER = "other"


class PantryItem(Base):
    """
    Represents a single item in the user's pantry.
    
    Design decisions:
    - `canonical_name`: Normalized name for matching (e.g., "whole milk" → "milk")
      This helps when comparing receipt items to existing inventory.
    - `quantity` as Float: Supports fractional amounts (0.5 lb, 2.5 cups)
    - `estimated_expiry`: Nullable because not all items have clear expiry
    - `source`: Tracks whether item came from manual entry or receipt scan
    """
    
    __tablename__ = "pantry_items"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # User association (for multi-user support later)
    # For MVP, we can use a default user_id = 1
    user_id: Mapped[int] = mapped_column(default=1, index=True)
    
    # Item identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Quantity tracking
    quantity: Mapped[float] = mapped_column(Float, default=1.0)
    unit: Mapped[str] = mapped_column(String(50), default="unit")  # "unit", "lb", "oz", "cups", etc.
    
    # Expiry and freshness
    estimated_expiry: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Organization
    category: Mapped[str] = mapped_column(
        String(50), 
        default=ItemCategory.OTHER.value
    )
    
    # Metadata
    source: Mapped[str] = mapped_column(
        String(20), 
        default=ItemSource.MANUAL.value
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Indexes for common queries
    __table_args__ = (
        # Fast lookup by user + category (for filtered views)
        Index("ix_pantry_user_category", "user_id", "category"),
        # Fast lookup for expiring items
        Index("ix_pantry_user_expiry", "user_id", "estimated_expiry"),
    )
    
    def __repr__(self) -> str:
        return f"<PantryItem(id={self.id}, name='{self.name}', qty={self.quantity} {self.unit})>"
