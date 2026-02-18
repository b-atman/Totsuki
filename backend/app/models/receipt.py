"""
ReceiptItem model - represents individual line items from uploaded receipts.

This model serves two purposes:
1. Price History - Track historical prices for items across stores and dates
2. Receipt Archive - Keep a permanent record of all uploaded receipts

Each row = one line item from a receipt (e.g., "Milk 1gal - $3.99")
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import DateTime, Float, Index, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.pantry import ItemCategory


def generate_batch_id() -> str:
    """Generate a unique batch ID for grouping receipt items from a single upload."""
    return str(uuid.uuid4())


class ReceiptItem(Base):
    """
    Represents a single line item from an uploaded grocery receipt.
    
    Design decisions:
    - `receipt_batch_id`: Groups items from the same receipt upload together.
      This allows viewing/deleting entire receipts as a unit.
    - `raw_name`: Original text from receipt (e.g., "GV 2% MILK 1GAL")
    - `normalized_name`: Cleaned name for matching (e.g., "milk")
    - `matched_pantry_item_id`: Links to pantry item if a match was found.
      Enables "undo" functionality and tracking which items were updated.
    - `total_price`: Pre-computed for faster aggregation queries.
    """
    
    __tablename__ = "receipt_items"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # User association (for multi-user support)
    user_id: Mapped[int] = mapped_column(default=1, index=True)
    
    # Receipt grouping - items from same upload share this ID
    receipt_batch_id: Mapped[str] = mapped_column(
        String(36),  # UUID length
        nullable=False,
        index=True
    )
    
    # Item identification
    raw_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original name from receipt"
    )
    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Cleaned name for matching"
    )
    
    # Quantity and pricing
    quantity: Mapped[float] = mapped_column(Float, default=1.0)
    unit: Mapped[str] = mapped_column(String(50), default="unit")
    unit_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Price per unit"
    )
    total_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="quantity * unit_price (pre-computed for aggregation)"
    )
    
    # Categorization
    category: Mapped[str] = mapped_column(
        String(50),
        default=ItemCategory.OTHER.value,
        index=True
    )
    
    # Store and date tracking
    store: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Store name (e.g., 'Walmart', 'Kroger')"
    )
    purchase_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Date of purchase"
    )
    
    # Pantry linkage (optional - set when item matches a pantry item)
    matched_pantry_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pantry_items.id", ondelete="SET NULL"),
        nullable=True,
        comment="Links to pantry item if matched during ingestion"
    )
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Indexes for common query patterns
    __table_args__ = (
        # Analytics: spend by user + category
        Index("ix_receipt_user_category", "user_id", "category"),
        # Analytics: spend by user + store
        Index("ix_receipt_user_store", "user_id", "store"),
        # Analytics: spend over time
        Index("ix_receipt_user_date", "user_id", "purchase_date"),
        # Price history: lookup by normalized name + store
        Index("ix_receipt_name_store", "normalized_name", "store"),
    )
    
    def __repr__(self) -> str:
        return f"<ReceiptItem(id={self.id}, name='{self.raw_name}', ${self.total_price:.2f})>"
