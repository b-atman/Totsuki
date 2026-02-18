"""
CRUD operations for ReceiptItem.

This module handles:
- Bulk creation of receipt items from CSV uploads
- Fetching receipts by batch ID
- Analytics queries for spend breakdowns
"""

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select, func, extract, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.receipt import ReceiptItem
from app.models.pantry import PantryItem


# =============================================================================
# Create Operations
# =============================================================================

async def create_receipt_items_bulk(
    db: AsyncSession,
    items: list[dict],
    batch_id: str,
    store: str,
    purchase_date: datetime,
    user_id: int = 1
) -> list[ReceiptItem]:
    """
    Create multiple receipt items in a single transaction.
    
    Args:
        db: Database session
        items: List of item dicts with keys: raw_name, normalized_name, 
               quantity, unit, unit_price, total_price, category, 
               matched_pantry_item_id (optional)
        batch_id: UUID grouping items from same upload
        store: Store name
        purchase_date: Date of purchase
        user_id: Owner of the items
    
    Returns:
        List of created ReceiptItem objects
    """
    db_items = []
    
    for item_data in items:
        db_item = ReceiptItem(
            user_id=user_id,
            receipt_batch_id=batch_id,
            raw_name=item_data["raw_name"],
            normalized_name=item_data["normalized_name"],
            quantity=item_data.get("quantity", 1.0),
            unit=item_data.get("unit", "unit"),
            unit_price=item_data["unit_price"],
            total_price=item_data["total_price"],
            category=item_data.get("category", "other"),
            store=store,
            purchase_date=purchase_date,
            matched_pantry_item_id=item_data.get("matched_pantry_item_id"),
        )
        db.add(db_item)
        db_items.append(db_item)
    
    await db.flush()
    
    for item in db_items:
        await db.refresh(item)
    
    return db_items


# =============================================================================
# Read Operations
# =============================================================================

async def get_receipt_item(
    db: AsyncSession,
    item_id: int,
    user_id: int = 1
) -> Optional[ReceiptItem]:
    """Get a single receipt item by ID."""
    query = select(ReceiptItem).where(
        ReceiptItem.id == item_id,
        ReceiptItem.user_id == user_id
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_items_by_batch(
    db: AsyncSession,
    batch_id: str,
    user_id: int = 1
) -> Sequence[ReceiptItem]:
    """Get all receipt items from a specific batch (single receipt upload)."""
    query = select(ReceiptItem).where(
        ReceiptItem.receipt_batch_id == batch_id,
        ReceiptItem.user_id == user_id
    ).order_by(ReceiptItem.id)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_recent_receipts(
    db: AsyncSession,
    user_id: int = 1,
    limit: int = 10
) -> list[dict]:
    """
    Get list of recent receipt batches (grouped uploads).
    
    Returns summary info for each batch: batch_id, store, date, total, item_count
    """
    query = (
        select(
            ReceiptItem.receipt_batch_id,
            ReceiptItem.store,
            ReceiptItem.purchase_date,
            func.sum(ReceiptItem.total_price).label("total_amount"),
            func.count(ReceiptItem.id).label("item_count"),
        )
        .where(ReceiptItem.user_id == user_id)
        .group_by(
            ReceiptItem.receipt_batch_id,
            ReceiptItem.store,
            ReceiptItem.purchase_date,
        )
        .order_by(desc(ReceiptItem.purchase_date))
        .limit(limit)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "batch_id": row.receipt_batch_id,
            "store": row.store,
            "purchase_date": row.purchase_date,
            "total_amount": row.total_amount,
            "item_count": row.item_count,
        }
        for row in rows
    ]


# =============================================================================
# Analytics Queries
# =============================================================================

async def get_spend_by_category(
    db: AsyncSession,
    user_id: int = 1,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> list[dict]:
    """
    Get total spending grouped by category.
    
    Returns list of dicts with: category, total_spent, item_count
    """
    query = (
        select(
            ReceiptItem.category,
            func.sum(ReceiptItem.total_price).label("total_spent"),
            func.count(ReceiptItem.id).label("item_count"),
        )
        .where(ReceiptItem.user_id == user_id)
        .group_by(ReceiptItem.category)
        .order_by(desc("total_spent"))
    )
    
    if start_date:
        query = query.where(ReceiptItem.purchase_date >= start_date)
    if end_date:
        query = query.where(ReceiptItem.purchase_date <= end_date)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "category": row.category,
            "total_spent": float(row.total_spent or 0),
            "item_count": row.item_count,
        }
        for row in rows
    ]


async def get_spend_by_store(
    db: AsyncSession,
    user_id: int = 1,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> list[dict]:
    """
    Get total spending grouped by store.
    
    Returns list of dicts with: store, total_spent, visit_count
    """
    query = (
        select(
            ReceiptItem.store,
            func.sum(ReceiptItem.total_price).label("total_spent"),
            func.count(func.distinct(ReceiptItem.receipt_batch_id)).label("visit_count"),
        )
        .where(ReceiptItem.user_id == user_id)
        .group_by(ReceiptItem.store)
        .order_by(desc("total_spent"))
    )
    
    if start_date:
        query = query.where(ReceiptItem.purchase_date >= start_date)
    if end_date:
        query = query.where(ReceiptItem.purchase_date <= end_date)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "store": row.store,
            "total_spent": float(row.total_spent or 0),
            "visit_count": row.visit_count,
        }
        for row in rows
    ]


async def get_spend_by_month(
    db: AsyncSession,
    user_id: int = 1,
    months: int = 12
) -> list[dict]:
    """
    Get total spending grouped by month.
    
    Args:
        db: Database session
        user_id: Owner filter
        months: Number of months to look back
    
    Returns list of dicts with: month (YYYY-MM), total_spent, item_count
    """
    query = (
        select(
            func.strftime("%Y-%m", ReceiptItem.purchase_date).label("month"),
            func.sum(ReceiptItem.total_price).label("total_spent"),
            func.count(ReceiptItem.id).label("item_count"),
        )
        .where(ReceiptItem.user_id == user_id)
        .group_by("month")
        .order_by("month")
        .limit(months)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "month": row.month,
            "total_spent": float(row.total_spent or 0),
            "item_count": row.item_count,
        }
        for row in rows
    ]


async def get_top_items_by_spending(
    db: AsyncSession,
    user_id: int = 1,
    limit: int = 10,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> list[dict]:
    """
    Get top items by total spending.
    
    Groups by normalized_name to aggregate variations of same item.
    """
    query = (
        select(
            ReceiptItem.normalized_name,
            func.sum(ReceiptItem.total_price).label("total_spent"),
            func.sum(ReceiptItem.quantity).label("total_quantity"),
            func.count(ReceiptItem.id).label("purchase_count"),
            func.avg(ReceiptItem.unit_price).label("avg_price"),
        )
        .where(ReceiptItem.user_id == user_id)
        .group_by(ReceiptItem.normalized_name)
        .order_by(desc("total_spent"))
        .limit(limit)
    )
    
    if start_date:
        query = query.where(ReceiptItem.purchase_date >= start_date)
    if end_date:
        query = query.where(ReceiptItem.purchase_date <= end_date)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "name": row.normalized_name,
            "total_spent": float(row.total_spent or 0),
            "total_quantity": float(row.total_quantity or 0),
            "purchase_count": row.purchase_count,
            "avg_price": float(row.avg_price or 0),
        }
        for row in rows
    ]


async def get_spending_summary(
    db: AsyncSession,
    user_id: int = 1,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> dict:
    """
    Get overall spending summary statistics.
    
    Returns: total_spent, total_items, total_receipts, date_range
    """
    query = (
        select(
            func.sum(ReceiptItem.total_price).label("total_spent"),
            func.count(ReceiptItem.id).label("total_items"),
            func.count(func.distinct(ReceiptItem.receipt_batch_id)).label("total_receipts"),
            func.min(ReceiptItem.purchase_date).label("earliest_date"),
            func.max(ReceiptItem.purchase_date).label("latest_date"),
        )
        .where(ReceiptItem.user_id == user_id)
    )
    
    if start_date:
        query = query.where(ReceiptItem.purchase_date >= start_date)
    if end_date:
        query = query.where(ReceiptItem.purchase_date <= end_date)
    
    result = await db.execute(query)
    row = result.one()
    
    return {
        "total_spent": float(row.total_spent or 0),
        "total_items": row.total_items or 0,
        "total_receipts": row.total_receipts or 0,
        "date_range_start": row.earliest_date,
        "date_range_end": row.latest_date,
    }


# =============================================================================
# Delete Operations
# =============================================================================

async def delete_receipt_batch(
    db: AsyncSession,
    batch_id: str,
    user_id: int = 1
) -> int:
    """
    Delete all receipt items from a batch.
    
    Returns: Number of items deleted
    """
    items = await get_items_by_batch(db, batch_id, user_id)
    count = len(items)
    
    for item in items:
        await db.delete(item)
    
    await db.flush()
    return count


# =============================================================================
# Pantry Matching Helpers
# =============================================================================

async def get_all_pantry_items_for_matching(
    db: AsyncSession,
    user_id: int = 1
) -> list[dict]:
    """
    Get all pantry items in format suitable for name matching.
    
    Returns list of dicts with: id, name, canonical_name, category
    """
    query = select(
        PantryItem.id,
        PantryItem.name,
        PantryItem.canonical_name,
        PantryItem.category,
    ).where(PantryItem.user_id == user_id)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        {
            "id": row.id,
            "name": row.name,
            "canonical_name": row.canonical_name,
            "category": row.category,
        }
        for row in rows
    ]
