"""
Receipt Ingestion API routes.

Endpoints:
- POST   /ingest-receipt          - Upload CSV and get preview
- POST   /ingest-receipt/confirm  - Confirm and save receipt
- GET    /analytics/spend-breakdown - Get spending analytics
- GET    /receipts                - List recent receipts
- DELETE /receipts/{batch_id}     - Delete a receipt batch
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import receipt as receipt_crud
from app.crud import pantry as pantry_crud
from app.models.pantry import ItemSource
from app.schemas.pantry import PantryItemCreate
from app.schemas.receipt import (
    CSVParseResponse,
    ReceiptConfirmRequest,
    ReceiptIngestionResponse,
    ReceiptItemResponse,
    SpendBreakdownResponse,
)
from app.services.receipt import (
    parse_csv_content,
    create_receipt_preview,
    prepare_receipt_items_for_db,
    prepare_pantry_updates,
    build_spend_breakdown,
)


router = APIRouter(tags=["Receipts"])

DEFAULT_USER_ID = 1


# =============================================================================
# POST /ingest-receipt - Upload and parse CSV
# =============================================================================

@router.post(
    "/ingest-receipt",
    response_model=CSVParseResponse,
    summary="Upload receipt CSV",
    description="Upload a CSV file with receipt items. Returns parsed preview for confirmation.",
)
async def upload_receipt(
    file: UploadFile = File(..., description="CSV file with receipt items"),
    store: str = Form(..., description="Store name (e.g., 'Walmart')"),
    purchase_date: datetime = Form(..., description="Date of purchase (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
) -> CSVParseResponse:
    """
    Upload a receipt CSV and get a preview of parsed items.
    
    The CSV should have columns for item name, quantity, unit, and price.
    Column names are auto-detected from headers.
    
    Returns a preview with:
    - Normalized item names
    - Matched pantry items (if any)
    - Inferred categories
    - Total amounts
    
    Use the returned batch_id to confirm the receipt.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )
    
    try:
        content = await file.read()
        csv_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded"
        )
    
    parsed_items = parse_csv_content(csv_content)
    
    if not parsed_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid items found in CSV. Check column headers (name, qty, price)."
        )
    
    pantry_items = await receipt_crud.get_all_pantry_items_for_matching(
        db, user_id=DEFAULT_USER_ID
    )
    
    preview = create_receipt_preview(
        parsed_items=parsed_items,
        pantry_items=pantry_items,
        store=store,
        purchase_date=purchase_date,
    )
    
    return preview


# =============================================================================
# POST /ingest-receipt/confirm - Confirm and save receipt
# =============================================================================

@router.post(
    "/ingest-receipt/confirm",
    response_model=ReceiptIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm receipt upload",
    description="Confirm a parsed receipt to save items and update pantry.",
)
async def confirm_receipt(
    request: ReceiptConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> ReceiptIngestionResponse:
    """
    Confirm a receipt after reviewing the preview.
    
    This will:
    1. Save all receipt items to the database (price history)
    2. Update matched pantry item quantities
    3. Create new pantry items for unmatched items (if update_pantry=true)
    
    Returns summary of what was created/updated.
    """
    pantry_items = await receipt_crud.get_all_pantry_items_for_matching(
        db, user_id=DEFAULT_USER_ID
    )
    
    preview = create_receipt_preview(
        parsed_items=[
            {
                "raw_name": item.raw_name,
                "quantity": item.quantity,
                "unit": item.unit,
                "unit_price": item.unit_price,
                "category": item.category.value if hasattr(item.category, 'value') else item.category,
            }
            for item in request.items
        ],
        pantry_items=pantry_items,
        store=request.store,
        purchase_date=request.purchase_date,
    )
    
    preview.batch_id = request.batch_id
    
    items_for_db = prepare_receipt_items_for_db(preview.items)
    
    await receipt_crud.create_receipt_items_bulk(
        db=db,
        items=items_for_db,
        batch_id=request.batch_id,
        store=request.store,
        purchase_date=request.purchase_date,
        user_id=DEFAULT_USER_ID,
    )
    
    pantry_updated = 0
    pantry_created = 0
    
    if request.update_pantry:
        updates, creates = prepare_pantry_updates(preview.items)
        
        for update in updates:
            pantry_item = await pantry_crud.get_item(
                db, update["pantry_id"], user_id=DEFAULT_USER_ID
            )
            if pantry_item:
                pantry_item.quantity += update["quantity_to_add"]
                await db.flush()
                pantry_updated += 1
        
        for create_data in creates:
            new_item = PantryItemCreate(
                name=create_data["name"],
                canonical_name=create_data["canonical_name"],
                quantity=create_data["quantity"],
                unit=create_data["unit"],
                category=create_data["category"],
                source=ItemSource.RECEIPT,
            )
            await pantry_crud.create_item(db, new_item, user_id=DEFAULT_USER_ID)
            pantry_created += 1
    
    return ReceiptIngestionResponse(
        batch_id=request.batch_id,
        items_created=len(items_for_db),
        pantry_items_updated=pantry_updated,
        pantry_items_created=pantry_created,
        total_amount=preview.total_amount,
        message=f"Receipt saved. {pantry_updated} pantry items updated, {pantry_created} new items created.",
    )


# =============================================================================
# GET /analytics/spend-breakdown - Spending analytics
# =============================================================================

@router.get(
    "/analytics/spend-breakdown",
    response_model=SpendBreakdownResponse,
    summary="Get spending breakdown",
    description="Get spending analytics grouped by category, store, and month.",
)
async def get_spend_breakdown(
    start_date: Optional[datetime] = Query(
        default=None,
        description="Filter start date (ISO 8601)"
    ),
    end_date: Optional[datetime] = Query(
        default=None,
        description="Filter end date (ISO 8601)"
    ),
    db: AsyncSession = Depends(get_db),
) -> SpendBreakdownResponse:
    """
    Get comprehensive spending analytics.
    
    Returns:
    - Total spending summary
    - Breakdown by category (for pie chart)
    - Breakdown by store (for pie chart)
    - Breakdown by month (for line chart)
    - Top items by spending
    """
    summary = await receipt_crud.get_spending_summary(
        db, user_id=DEFAULT_USER_ID,
        start_date=start_date, end_date=end_date
    )
    
    by_category = await receipt_crud.get_spend_by_category(
        db, user_id=DEFAULT_USER_ID,
        start_date=start_date, end_date=end_date
    )
    
    by_store = await receipt_crud.get_spend_by_store(
        db, user_id=DEFAULT_USER_ID,
        start_date=start_date, end_date=end_date
    )
    
    by_month = await receipt_crud.get_spend_by_month(
        db, user_id=DEFAULT_USER_ID, months=12
    )
    
    top_items = await receipt_crud.get_top_items_by_spending(
        db, user_id=DEFAULT_USER_ID, limit=10,
        start_date=start_date, end_date=end_date
    )
    
    return build_spend_breakdown(
        summary=summary,
        by_category=by_category,
        by_store=by_store,
        by_month=by_month,
        top_items=top_items,
    )


# =============================================================================
# GET /receipts - List recent receipts
# =============================================================================

@router.get(
    "/receipts",
    summary="List recent receipts",
    description="Get a list of recent receipt uploads.",
)
async def list_receipts(
    limit: int = Query(default=10, ge=1, le=50, description="Number of receipts to return"),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    Get list of recent receipt batches.
    
    Returns summary for each batch: batch_id, store, date, total, item_count
    """
    return await receipt_crud.get_recent_receipts(
        db, user_id=DEFAULT_USER_ID, limit=limit
    )


# =============================================================================
# GET /receipts/{batch_id} - Get receipt details
# =============================================================================

@router.get(
    "/receipts/{batch_id}",
    response_model=list[ReceiptItemResponse],
    summary="Get receipt details",
    description="Get all items from a specific receipt batch.",
)
async def get_receipt_details(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ReceiptItemResponse]:
    """Get all items from a receipt batch."""
    items = await receipt_crud.get_items_by_batch(
        db, batch_id=batch_id, user_id=DEFAULT_USER_ID
    )
    
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt batch {batch_id} not found"
        )
    
    return [ReceiptItemResponse.model_validate(item) for item in items]


# =============================================================================
# DELETE /receipts/{batch_id} - Delete a receipt
# =============================================================================

@router.delete(
    "/receipts/{batch_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete receipt",
    description="Delete all items from a receipt batch.",
)
async def delete_receipt(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Delete a receipt batch and all its items.
    
    Note: This does NOT undo pantry updates. Use with caution.
    """
    count = await receipt_crud.delete_receipt_batch(
        db, batch_id=batch_id, user_id=DEFAULT_USER_ID
    )
    
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt batch {batch_id} not found"
        )
    
    return {"message": f"Deleted {count} items from receipt batch", "batch_id": batch_id}
