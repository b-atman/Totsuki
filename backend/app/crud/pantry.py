"""
CRUD operations for PantryItem.

This module contains all database operations for pantry items:
- Create, Read, Update, Delete
- Consume (reduce quantity with auto-delete at zero)
- List with optional filtering
"""

from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pantry import PantryItem
from app.schemas.pantry import PantryItemCreate, PantryItemUpdate


async def create_item(
    db: AsyncSession,
    item_data: PantryItemCreate,
    user_id: int = 1
) -> PantryItem:
    """
    Create a new pantry item.
    
    Args:
        db: Database session
        item_data: Validated item data from request
        user_id: Owner of the item (default 1 for MVP)
    
    Returns:
        The created PantryItem with generated id and timestamps
    """
    # Convert Pydantic model to dict, then to SQLAlchemy model
    item_dict = item_data.model_dump()
    
    # Convert enum to string value for database storage
    item_dict["category"] = item_data.category.value
    item_dict["source"] = item_data.source.value
    
    # Auto-generate canonical_name if not provided
    if not item_dict.get("canonical_name"):
        item_dict["canonical_name"] = _normalize_name(item_data.name)
    
    db_item = PantryItem(**item_dict, user_id=user_id)
    
    db.add(db_item)
    await db.flush()  # Get the generated ID without committing
    await db.refresh(db_item)  # Load all fields including defaults
    
    return db_item


async def get_item(
    db: AsyncSession,
    item_id: int,
    user_id: int = 1
) -> Optional[PantryItem]:
    """
    Get a single pantry item by ID.
    
    Args:
        db: Database session
        item_id: The item's primary key
        user_id: Owner filter (ensures users only see their items)
    
    Returns:
        PantryItem if found, None otherwise
    """
    query = select(PantryItem).where(
        PantryItem.id == item_id,
        PantryItem.user_id == user_id
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_items(
    db: AsyncSession,
    user_id: int = 1,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[Sequence[PantryItem], int]:
    """
    Get all pantry items for a user with optional filtering.
    
    Args:
        db: Database session
        user_id: Owner filter
        category: Optional category filter
        skip: Offset for pagination
        limit: Max items to return
    
    Returns:
        Tuple of (items list, total count)
    """
    # Base query
    query = select(PantryItem).where(PantryItem.user_id == user_id)
    count_query = select(func.count(PantryItem.id)).where(PantryItem.user_id == user_id)
    
    # Apply category filter if provided
    if category:
        query = query.where(PantryItem.category == category)
        count_query = count_query.where(PantryItem.category == category)
    
    # Order by last_updated (most recent first)
    query = query.order_by(PantryItem.last_updated.desc())
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute both queries
    result = await db.execute(query)
    items = result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    return items, total


async def update_item(
    db: AsyncSession,
    item_id: int,
    item_data: PantryItemUpdate,
    user_id: int = 1
) -> Optional[PantryItem]:
    """
    Update an existing pantry item.
    
    Only updates fields that are explicitly provided (not None).
    
    Args:
        db: Database session
        item_id: The item to update
        item_data: Fields to update
        user_id: Owner filter
    
    Returns:
        Updated PantryItem if found, None if not found
    """
    # First, fetch the existing item
    db_item = await get_item(db, item_id, user_id)
    if not db_item:
        return None
    
    # Get only the fields that were explicitly set
    update_data = item_data.model_dump(exclude_unset=True)
    
    # Convert enum to string if category was provided
    if "category" in update_data and update_data["category"] is not None:
        update_data["category"] = update_data["category"].value
    
    # Update canonical_name if name changed and canonical_name not provided
    if "name" in update_data and "canonical_name" not in update_data:
        update_data["canonical_name"] = _normalize_name(update_data["name"])
    
    # Apply updates
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    await db.flush()
    await db.refresh(db_item)
    
    return db_item


async def delete_item(
    db: AsyncSession,
    item_id: int,
    user_id: int = 1
) -> bool:
    """
    Delete a pantry item.
    
    Args:
        db: Database session
        item_id: The item to delete
        user_id: Owner filter
    
    Returns:
        True if item was deleted, False if not found
    """
    db_item = await get_item(db, item_id, user_id)
    if not db_item:
        return False
    
    await db.delete(db_item)
    await db.flush()
    
    return True


async def consume_item(
    db: AsyncSession,
    item_id: int,
    quantity: float,
    user_id: int = 1
) -> Optional[PantryItem]:
    """
    Consume (use) a quantity of a pantry item.
    
    Business rules:
    - Reduces quantity by the specified amount
    - If quantity reaches 0 or below, item is deleted
    - Cannot consume more than available (but will delete if over)
    
    Args:
        db: Database session
        item_id: The item to consume
        quantity: Amount to consume
        user_id: Owner filter
    
    Returns:
        Updated PantryItem if still exists, None if deleted or not found
    """
    db_item = await get_item(db, item_id, user_id)
    if not db_item:
        return None
    
    # Reduce quantity
    new_quantity = db_item.quantity - quantity
    
    if new_quantity <= 0:
        # Delete the item if quantity is zero or negative
        await db.delete(db_item)
        await db.flush()
        return None  # Item was consumed completely
    
    # Update the quantity
    db_item.quantity = new_quantity
    await db.flush()
    await db.refresh(db_item)
    
    return db_item


def _normalize_name(name: str) -> str:
    """
    Create a normalized/canonical version of an item name.
    
    This helps with matching items from receipts to existing inventory.
    For now, just lowercase and strip. Later, can add:
    - Remove brand names
    - Singularize plurals
    - Remove size descriptors
    
    Examples:
        "Organic Whole Milk 1 Gallon" -> "organic whole milk 1 gallon"
        "  Chicken Breast  " -> "chicken breast"
    """
    return name.lower().strip()
