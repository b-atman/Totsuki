"""
Inventory API routes for pantry management.

Endpoints:
- POST   /inventory/item     - Add a new item
- GET    /inventory          - List all items
- PUT    /inventory/item/{id} - Update an item
- DELETE /inventory/item/{id} - Delete an item
- POST   /inventory/consume   - Consume (use) an item
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import pantry as pantry_crud
from app.models.pantry import ItemCategory
from app.schemas.pantry import (
    PantryItemCreate,
    PantryItemUpdate,
    PantryItemConsume,
    PantryItemResponse,
    PantryListResponse,
)


# Create router with prefix and tags for OpenAPI docs
router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"],
)

# Default user ID for MVP (will be replaced with auth later)
DEFAULT_USER_ID = 1


# =============================================================================
# POST /inventory/item - Create a new item
# =============================================================================

@router.post(
    "/item",
    response_model=PantryItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to pantry",
    description="Create a new pantry item. Returns the created item with generated ID.",
)
async def create_inventory_item(
    item: PantryItemCreate,
    db: AsyncSession = Depends(get_db),
) -> PantryItemResponse:
    """
    Add a new item to the pantry.
    
    - **name**: Required. Name of the item (e.g., "Whole Milk")
    - **quantity**: Amount (default: 1.0)
    - **unit**: Unit of measurement (default: "unit")
    - **category**: Grocery category (default: "other")
    - **estimated_expiry**: Optional expiration date
    """
    db_item = await pantry_crud.create_item(db, item, user_id=DEFAULT_USER_ID)
    return PantryItemResponse.model_validate(db_item)


# =============================================================================
# GET /inventory - List all items
# =============================================================================

@router.get(
    "",
    response_model=PantryListResponse,
    summary="List pantry items",
    description="Get all items in the pantry with optional filtering.",
)
async def list_inventory(
    category: Optional[ItemCategory] = Query(
        default=None,
        description="Filter by category"
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of items to skip (pagination)"
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Maximum items to return"
    ),
    db: AsyncSession = Depends(get_db),
) -> PantryListResponse:
    """
    List all pantry items for the current user.
    
    - **category**: Optional filter (e.g., "dairy", "produce")
    - **skip**: Pagination offset
    - **limit**: Max items per page (1-1000)
    
    Returns items sorted by last_updated (most recent first).
    """
    # Convert enum to string value for query
    category_value = category.value if category else None
    
    items, total = await pantry_crud.get_items(
        db,
        user_id=DEFAULT_USER_ID,
        category=category_value,
        skip=skip,
        limit=limit,
    )
    
    return PantryListResponse(
        items=[PantryItemResponse.model_validate(item) for item in items],
        total=total,
    )


# =============================================================================
# PUT /inventory/item/{id} - Update an item
# =============================================================================

@router.put(
    "/item/{item_id}",
    response_model=PantryItemResponse,
    summary="Update pantry item",
    description="Update an existing pantry item. Only provided fields are changed.",
)
async def update_inventory_item(
    item_id: int,
    item: PantryItemUpdate,
    db: AsyncSession = Depends(get_db),
) -> PantryItemResponse:
    """
    Update an existing pantry item.
    
    Supports partial updates - only include fields you want to change.
    """
    db_item = await pantry_crud.update_item(
        db,
        item_id=item_id,
        item_data=item,
        user_id=DEFAULT_USER_ID,
    )
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found",
        )
    
    return PantryItemResponse.model_validate(db_item)


# =============================================================================
# DELETE /inventory/item/{id} - Delete an item
# =============================================================================

@router.delete(
    "/item/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete pantry item",
    description="Remove an item from the pantry.",
)
async def delete_inventory_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a pantry item by ID.
    
    Returns 204 No Content on success, 404 if item not found.
    """
    deleted = await pantry_crud.delete_item(
        db,
        item_id=item_id,
        user_id=DEFAULT_USER_ID,
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found",
        )


# =============================================================================
# POST /inventory/consume - Consume (use) an item
# =============================================================================

@router.post(
    "/consume",
    response_model=Optional[PantryItemResponse],
    summary="Consume pantry item",
    description="Use a quantity of an item. Auto-deletes if quantity reaches 0.",
)
async def consume_inventory_item(
    consume_data: PantryItemConsume,
    db: AsyncSession = Depends(get_db),
) -> Optional[PantryItemResponse]:
    """
    Consume (use) a quantity of a pantry item.
    
    - Reduces quantity by the specified amount
    - If quantity reaches 0, the item is automatically deleted
    - Returns the updated item, or null if item was fully consumed
    
    **Example:** You have 2 gallons of milk, consume 0.5, now you have 1.5.
    """
    # First check if item exists
    existing = await pantry_crud.get_item(
        db,
        item_id=consume_data.item_id,
        user_id=DEFAULT_USER_ID,
    )
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {consume_data.item_id} not found",
        )
    
    # Perform consumption
    db_item = await pantry_crud.consume_item(
        db,
        item_id=consume_data.item_id,
        quantity=consume_data.quantity,
        user_id=DEFAULT_USER_ID,
    )
    
    # Return updated item or None if fully consumed
    if db_item:
        return PantryItemResponse.model_validate(db_item)
    
    return None  # Item was fully consumed and deleted
