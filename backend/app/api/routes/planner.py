"""
Meal Planner API routes.

Endpoints:
- POST /plan/generate  - Generate a 7-day meal plan
- GET  /plan/cuisines  - Get available cuisine tags
- GET  /plan/diets     - Get available diet tags
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.recipe import get_recipes, get_all_cuisines, get_all_diets
from app.services.planner import generate_meal_plan
from app.schemas.planner import PlanRequest, PlanResponse


router = APIRouter(
    prefix="/plan",
    tags=["Meal Planner"],
)


# =============================================================================
# POST /plan/generate - Generate meal plan
# =============================================================================

@router.post(
    "/generate",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate meal plan",
    description="Generate a personalized 7-day meal plan based on preferences and constraints.",
)
async def generate_plan(
    request: PlanRequest,
    db: AsyncSession = Depends(get_db),
) -> PlanResponse:
    """
    Generate a 7-day meal plan.
    
    **Request Parameters:**
    - **budget**: Max weekly budget in $ (optional)
    - **max_time**: Max cooking time per meal in minutes (default: 60)
    - **protein_goal**: Target protein per meal in grams (optional)
    - **diet_tags**: Required dietary tags like "vegetarian" (optional)
    - **cuisine_preferences**: Preferred cuisines like "italian" (optional)
    - **servings_per_day**: Meals per day, 1-3 (default: 1)
    
    **Response:**
    - 7-day meal plan with recipes
    - Aggregated shopping list
    - Summary statistics (cost, protein, calories)
    
    **Example Request:**
    ```json
    {
        "budget": 75,
        "max_time": 45,
        "protein_goal": 30,
        "diet_tags": ["gluten-free"],
        "cuisine_preferences": ["italian", "mexican"]
    }
    ```
    """
    # Fetch all recipes from database
    recipes, total = await get_recipes(db, limit=1000)
    
    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No recipes available. Please try again later.",
        )
    
    # Generate the meal plan
    plan = generate_meal_plan(recipes, request)
    
    return plan


# =============================================================================
# GET /plan/cuisines - Get available cuisines
# =============================================================================

@router.get(
    "/cuisines",
    response_model=list[str],
    summary="Get available cuisines",
    description="Get all unique cuisine tags from the recipe database.",
)
async def list_cuisines(
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    """
    Get available cuisine tags for filtering.
    
    Returns a sorted list of unique cuisines like:
    `["american", "asian", "italian", "mexican", ...]`
    
    Use these values in the `cuisine_preferences` field when generating a plan.
    """
    cuisines = await get_all_cuisines(db)
    return cuisines


# =============================================================================
# GET /plan/diets - Get available diet tags
# =============================================================================

@router.get(
    "/diets",
    response_model=list[str],
    summary="Get available diet tags",
    description="Get all unique diet tags from the recipe database.",
)
async def list_diets(
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    """
    Get available diet tags for filtering.
    
    Returns a sorted list of unique diet tags like:
    `["gluten-free", "high-protein", "vegetarian", "vegan", ...]`
    
    Use these values in the `diet_tags` field when generating a plan.
    """
    diets = await get_all_diets(db)
    return diets
