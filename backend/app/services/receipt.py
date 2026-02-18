"""
Receipt Ingestion Service.

This module handles the business logic for receipt processing:
1. Parse CSV files into structured items
2. Normalize names and match to existing pantry items
3. Infer categories from item names
4. Build preview responses for user confirmation
5. Process confirmed receipts and update pantry
6. Aggregate analytics data for charts
"""

import csv
import io
from datetime import datetime
from typing import Optional

from app.models.pantry import ItemCategory, ItemSource
from app.models.receipt import generate_batch_id
from app.utils.normalize import normalize_item_name, find_best_match, suggest_canonical_name
from app.schemas.receipt import (
    ReceiptItemPreview,
    CSVParseResponse,
    ReceiptIngestionResponse,
    SpendByCategory,
    SpendByStore,
    SpendByMonth,
    SpendBreakdownResponse,
)


# =============================================================================
# Category Inference
# =============================================================================

CATEGORY_KEYWORDS = {
    ItemCategory.PRODUCE.value: [
        "apple", "banana", "orange", "lettuce", "spinach", "tomato", "potato",
        "onion", "carrot", "celery", "broccoli", "pepper", "cucumber", "avocado",
        "lemon", "lime", "grape", "berry", "melon", "mango", "pear", "peach",
        "mushroom", "garlic", "ginger", "herb", "cilantro", "parsley", "basil",
    ],
    ItemCategory.DAIRY.value: [
        "milk", "cheese", "yogurt", "butter", "cream", "egg", "sour cream",
        "cottage", "mozzarella", "cheddar", "parmesan", "feta", "ricotta",
    ],
    ItemCategory.MEAT.value: [
        "chicken", "beef", "pork", "turkey", "lamb", "bacon", "sausage",
        "ham", "steak", "ground", "breast", "thigh", "wing", "rib",
    ],
    ItemCategory.SEAFOOD.value: [
        "salmon", "tuna", "shrimp", "fish", "crab", "lobster", "tilapia",
        "cod", "halibut", "scallop", "oyster", "clam", "mussel",
    ],
    ItemCategory.BAKERY.value: [
        "bread", "bagel", "muffin", "croissant", "roll", "bun", "tortilla",
        "pita", "cake", "cookie", "donut", "pastry",
    ],
    ItemCategory.FROZEN.value: [
        "frozen", "ice cream", "pizza", "fries", "nugget", "waffle",
    ],
    ItemCategory.PANTRY.value: [
        "rice", "pasta", "noodle", "bean", "lentil", "flour", "sugar",
        "oil", "vinegar", "sauce", "soup", "broth", "canned", "cereal",
        "oat", "granola", "nut", "peanut", "almond",
    ],
    ItemCategory.BEVERAGES.value: [
        "water", "juice", "soda", "coffee", "tea", "beer", "wine",
        "drink", "beverage", "sparkling", "kombucha",
    ],
    ItemCategory.SNACKS.value: [
        "chip", "cracker", "pretzel", "popcorn", "candy", "chocolate",
        "bar", "trail mix", "snack",
    ],
    ItemCategory.CONDIMENTS.value: [
        "ketchup", "mustard", "mayo", "mayonnaise", "dressing", "salsa",
        "hot sauce", "soy sauce", "bbq", "relish", "pickle",
    ],
    ItemCategory.SPICES.value: [
        "salt", "pepper", "spice", "seasoning", "cumin", "paprika",
        "oregano", "thyme", "cinnamon", "nutmeg", "curry",
    ],
}


def infer_category(normalized_name: str) -> str:
    """
    Infer item category from normalized name using keyword matching.
    
    Returns the category with most keyword matches, or 'other' if no matches.
    """
    name_lower = normalized_name.lower()
    
    best_category = ItemCategory.OTHER.value
    best_score = 0
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in name_lower)
        if score > best_score:
            best_score = score
            best_category = category
    
    return best_category


# =============================================================================
# CSV Parsing
# =============================================================================

def parse_csv_content(
    csv_content: str,
    has_header: bool = True
) -> list[dict]:
    """
    Parse CSV content into list of item dicts.
    
    Expected CSV columns (flexible order):
    - name/item/description: Item name (required)
    - qty/quantity/amount: Quantity (default: 1)
    - unit: Unit of measure (default: "unit")
    - price/unit_price: Price per unit (required)
    - category: Item category (optional, will be inferred)
    
    Args:
        csv_content: Raw CSV string
        has_header: Whether first row is headers
    
    Returns:
        List of dicts with keys: raw_name, quantity, unit, unit_price, category
    """
    items = []
    
    reader = csv.reader(io.StringIO(csv_content))
    rows = list(reader)
    
    if not rows:
        return items
    
    # Detect column mapping from header or use defaults
    if has_header and rows:
        header = [col.lower().strip() for col in rows[0]]
        data_rows = rows[1:]
        col_map = _detect_column_mapping(header)
    else:
        data_rows = rows
        col_map = {"name": 0, "quantity": 1, "unit": 2, "price": 3}
    
    for row in data_rows:
        if not row or all(not cell.strip() for cell in row):
            continue
        
        try:
            item = _parse_row(row, col_map)
            if item:
                items.append(item)
        except (ValueError, IndexError):
            continue
    
    return items


def _detect_column_mapping(header: list[str]) -> dict:
    """Detect which columns contain which data based on header names."""
    col_map = {}
    
    name_variants = ["name", "item", "description", "product", "desc"]
    qty_variants = ["qty", "quantity", "amount", "count"]
    unit_variants = ["unit", "uom", "measure"]
    price_variants = ["price", "unit_price", "cost", "amount", "total"]
    category_variants = ["category", "cat", "type", "dept", "department"]
    
    for i, col in enumerate(header):
        col_lower = col.lower().strip()
        
        if any(v in col_lower for v in name_variants) and "name" not in col_map:
            col_map["name"] = i
        elif any(v in col_lower for v in qty_variants) and "quantity" not in col_map:
            col_map["quantity"] = i
        elif any(v in col_lower for v in unit_variants) and "unit" not in col_map:
            col_map["unit"] = i
        elif any(v in col_lower for v in price_variants) and "price" not in col_map:
            col_map["price"] = i
        elif any(v in col_lower for v in category_variants) and "category" not in col_map:
            col_map["category"] = i
    
    return col_map


def _parse_row(row: list[str], col_map: dict) -> Optional[dict]:
    """Parse a single CSV row into an item dict."""
    name_idx = col_map.get("name", 0)
    
    if name_idx >= len(row) or not row[name_idx].strip():
        return None
    
    raw_name = row[name_idx].strip()
    
    # Parse quantity (default 1)
    quantity = 1.0
    if "quantity" in col_map and col_map["quantity"] < len(row):
        try:
            qty_str = row[col_map["quantity"]].strip()
            if qty_str:
                quantity = float(qty_str)
        except ValueError:
            pass
    
    # Parse unit (default "unit")
    unit = "unit"
    if "unit" in col_map and col_map["unit"] < len(row):
        unit_str = row[col_map["unit"]].strip()
        if unit_str:
            unit = unit_str.lower()
    
    # Parse price (required)
    price_idx = col_map.get("price")
    if price_idx is None or price_idx >= len(row):
        return None
    
    try:
        price_str = row[price_idx].strip().replace("$", "").replace(",", "")
        unit_price = float(price_str)
    except ValueError:
        return None
    
    # Parse category (optional, will be inferred later)
    category = None
    if "category" in col_map and col_map["category"] < len(row):
        cat_str = row[col_map["category"]].strip().lower()
        if cat_str:
            category = cat_str
    
    return {
        "raw_name": raw_name,
        "quantity": quantity,
        "unit": unit,
        "unit_price": unit_price,
        "category": category,
    }


# =============================================================================
# Preview Generation
# =============================================================================

def create_receipt_preview(
    parsed_items: list[dict],
    pantry_items: list[dict],
    store: str,
    purchase_date: datetime,
) -> CSVParseResponse:
    """
    Create a preview response for parsed CSV items.
    
    This normalizes names, matches to pantry, infers categories,
    and builds a preview for user confirmation.
    
    Args:
        parsed_items: Items from parse_csv_content
        pantry_items: Current pantry items for matching
        store: Store name
        purchase_date: Purchase date
    
    Returns:
        CSVParseResponse with preview items and summary stats
    """
    batch_id = generate_batch_id()
    preview_items = []
    total_amount = 0.0
    matched_count = 0
    new_count = 0
    
    for item in parsed_items:
        # Normalize the name
        normalized = normalize_item_name(item["raw_name"])
        
        # Calculate total price
        total_price = item["quantity"] * item["unit_price"]
        total_amount += total_price
        
        # Try to match to existing pantry item
        match = find_best_match(item["raw_name"], pantry_items)
        
        # Infer category (use provided, matched, or inferred)
        if item.get("category"):
            category = _validate_category(item["category"])
        elif match and match.get("category"):
            category = match["category"]
        else:
            category = infer_category(normalized)
        
        # Build preview item
        preview = ReceiptItemPreview(
            raw_name=item["raw_name"],
            normalized_name=normalized,
            quantity=item["quantity"],
            unit=item["unit"],
            unit_price=item["unit_price"],
            total_price=total_price,
            category=ItemCategory(category),
            pantry_match_name=match.get("name") if match else None,
            pantry_match_id=match.get("id") if match else None,
            match_score=match.get("match_score") if match else None,
            will_create_new=match is None,
        )
        preview_items.append(preview)
        
        if match:
            matched_count += 1
        else:
            new_count += 1
    
    return CSVParseResponse(
        batch_id=batch_id,
        store=store,
        purchase_date=purchase_date,
        items=preview_items,
        total_items=len(preview_items),
        total_amount=total_amount,
        matched_count=matched_count,
        new_count=new_count,
    )


def _validate_category(category_str: str) -> str:
    """Validate and normalize category string to ItemCategory value."""
    category_lower = category_str.lower().strip()
    
    for cat in ItemCategory:
        if cat.value == category_lower:
            return cat.value
    
    return ItemCategory.OTHER.value


# =============================================================================
# Receipt Processing
# =============================================================================

def prepare_receipt_items_for_db(
    preview_items: list[ReceiptItemPreview],
) -> list[dict]:
    """
    Convert preview items to dicts ready for database insertion.
    """
    return [
        {
            "raw_name": item.raw_name,
            "normalized_name": item.normalized_name,
            "quantity": item.quantity,
            "unit": item.unit,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "category": item.category.value,
            "matched_pantry_item_id": item.pantry_match_id,
        }
        for item in preview_items
    ]


def prepare_pantry_updates(
    preview_items: list[ReceiptItemPreview],
) -> tuple[list[dict], list[dict]]:
    """
    Prepare pantry updates from confirmed receipt items.
    
    Returns:
        Tuple of (items_to_update, items_to_create)
        - items_to_update: [{pantry_id, quantity_to_add}]
        - items_to_create: [{name, canonical_name, quantity, unit, category}]
    """
    updates = []
    creates = []
    
    for item in preview_items:
        if item.pantry_match_id:
            updates.append({
                "pantry_id": item.pantry_match_id,
                "quantity_to_add": item.quantity,
            })
        else:
            creates.append({
                "name": item.raw_name,
                "canonical_name": item.normalized_name,
                "quantity": item.quantity,
                "unit": item.unit,
                "category": item.category.value,
                "source": ItemSource.RECEIPT.value,
            })
    
    return updates, creates


# =============================================================================
# Analytics
# =============================================================================

def build_spend_breakdown(
    summary: dict,
    by_category: list[dict],
    by_store: list[dict],
    by_month: list[dict],
    top_items: list[dict],
) -> SpendBreakdownResponse:
    """
    Build the complete spend breakdown response from CRUD results.
    
    Calculates percentages and formats data for frontend charts.
    """
    total_spent = summary.get("total_spent", 0) or 0
    
    # Add percentages to category breakdown
    category_data = [
        SpendByCategory(
            category=item["category"],
            total_spent=item["total_spent"],
            item_count=item["item_count"],
            percentage=(item["total_spent"] / total_spent * 100) if total_spent > 0 else 0,
        )
        for item in by_category
    ]
    
    # Add percentages to store breakdown
    store_data = [
        SpendByStore(
            store=item["store"],
            total_spent=item["total_spent"],
            visit_count=item["visit_count"],
            percentage=(item["total_spent"] / total_spent * 100) if total_spent > 0 else 0,
        )
        for item in by_store
    ]
    
    # Format month data
    month_data = [
        SpendByMonth(
            month=item["month"],
            total_spent=item["total_spent"],
            item_count=item["item_count"],
        )
        for item in by_month
    ]
    
    return SpendBreakdownResponse(
        total_spent=total_spent,
        total_items=summary.get("total_items", 0) or 0,
        total_receipts=summary.get("total_receipts", 0) or 0,
        date_range_start=summary.get("date_range_start"),
        date_range_end=summary.get("date_range_end"),
        by_category=category_data,
        by_store=store_data,
        by_month=month_data,
        top_items=top_items,
    )
