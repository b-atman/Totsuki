# CRUD operations
from app.crud.pantry import (
    create_item,
    get_item,
    get_items,
    update_item,
    delete_item,
    consume_item,
)
from app.crud.recipe import (
    get_recipe,
    get_recipes,
    get_recipe_count,
    seed_recipes,
    get_all_cuisines,
    get_all_diets,
)
from app.crud.receipt import (
    create_receipt_items_bulk,
    get_receipt_item,
    get_items_by_batch,
    get_recent_receipts,
    get_spend_by_category,
    get_spend_by_store,
    get_spend_by_month,
    get_top_items_by_spending,
    get_spending_summary,
    delete_receipt_batch,
    get_all_pantry_items_for_matching,
)

__all__ = [
    # Pantry CRUD
    "create_item",
    "get_item",
    "get_items",
    "update_item",
    "delete_item",
    "consume_item",
    # Recipe CRUD
    "get_recipe",
    "get_recipes",
    "get_recipe_count",
    "seed_recipes",
    "get_all_cuisines",
    "get_all_diets",
    # Receipt CRUD
    "create_receipt_items_bulk",
    "get_receipt_item",
    "get_items_by_batch",
    "get_recent_receipts",
    "get_spend_by_category",
    "get_spend_by_store",
    "get_spend_by_month",
    "get_top_items_by_spending",
    "get_spending_summary",
    "delete_receipt_batch",
    "get_all_pantry_items_for_matching",
]
