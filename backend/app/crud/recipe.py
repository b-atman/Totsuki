"""
CRUD operations for Recipe.

This module contains database operations for recipes:
- Read operations (get single, get list with filters)
- Seed operation (load initial recipes from JSON)

Recipes are pre-seeded data, so Create/Update/Delete are not needed for MVP.
"""

import json
from pathlib import Path
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe


async def get_recipe(
    db: AsyncSession,
    recipe_id: int
) -> Optional[Recipe]:
    """
    Get a single recipe by ID.
    
    Args:
        db: Database session
        recipe_id: The recipe's primary key
    
    Returns:
        Recipe if found, None otherwise
    """
    query = select(Recipe).where(Recipe.id == recipe_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_recipes(
    db: AsyncSession,
    cuisine: Optional[str] = None,
    diet: Optional[str] = None,
    max_time: Optional[int] = None,
    min_protein: Optional[float] = None,
    max_cost: Optional[float] = None,
    skip: int = 0,
    limit: int = 100
) -> tuple[Sequence[Recipe], int]:
    """
    Get recipes with optional filtering.
    
    Args:
        db: Database session
        cuisine: Filter by cuisine tag (e.g., "italian", "mexican")
        diet: Filter by diet tag (e.g., "vegetarian", "high-protein")
        max_time: Filter recipes that take <= this many minutes
        min_protein: Filter recipes with >= this much protein per serving
        max_cost: Filter recipes with <= this cost per serving
        skip: Offset for pagination
        limit: Max recipes to return
    
    Returns:
        Tuple of (recipes list, total count)
    """
    query = select(Recipe)
    count_query = select(func.count(Recipe.id))
    
    # Apply filters
    # Note: JSON array contains checks use SQLite JSON functions
    if cuisine:
        # Check if cuisine_tags JSON array contains the cuisine
        query = query.where(Recipe.cuisine_tags.contains(cuisine))
        count_query = count_query.where(Recipe.cuisine_tags.contains(cuisine))
    
    if diet:
        # Check if diet_tags JSON array contains the diet
        query = query.where(Recipe.diet_tags.contains(diet))
        count_query = count_query.where(Recipe.diet_tags.contains(diet))
    
    if max_time is not None:
        query = query.where(Recipe.time_minutes <= max_time)
        count_query = count_query.where(Recipe.time_minutes <= max_time)
    
    if min_protein is not None:
        query = query.where(Recipe.protein_estimate >= min_protein)
        count_query = count_query.where(Recipe.protein_estimate >= min_protein)
    
    if max_cost is not None:
        query = query.where(Recipe.estimated_cost <= max_cost)
        count_query = count_query.where(Recipe.estimated_cost <= max_cost)
    
    # Order by title
    query = query.order_by(Recipe.title)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute queries
    result = await db.execute(query)
    recipes = result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    return recipes, total


async def get_recipe_count(db: AsyncSession) -> int:
    """
    Get total number of recipes in database.
    
    Used to check if seeding is needed.
    
    Returns:
        Total recipe count
    """
    query = select(func.count(Recipe.id))
    result = await db.execute(query)
    return result.scalar() or 0


async def seed_recipes(db: AsyncSession) -> int:
    """
    Load recipes from seed JSON file into database.
    
    This should be called once during app startup if no recipes exist.
    
    Returns:
        Number of recipes seeded
    """
    # Path to seed data file
    seed_file = Path(__file__).parent.parent / "data" / "recipes_seed.json"
    
    if not seed_file.exists():
        print(f"Warning: Seed file not found at {seed_file}")
        return 0
    
    # Load JSON data
    with open(seed_file, "r", encoding="utf-8") as f:
        recipes_data = json.load(f)
    
    # Create Recipe objects
    count = 0
    for recipe_dict in recipes_data:
        recipe = Recipe(
            title=recipe_dict["title"],
            description=recipe_dict.get("description"),
            servings=recipe_dict.get("servings", 4),
            time_minutes=recipe_dict.get("time_minutes", 30),
            ingredients=recipe_dict.get("ingredients", []),
            steps=recipe_dict.get("steps", []),
            cuisine_tags=recipe_dict.get("cuisine_tags", []),
            diet_tags=recipe_dict.get("diet_tags", []),
            protein_estimate=recipe_dict.get("protein_estimate", 0.0),
            calorie_estimate=recipe_dict.get("calorie_estimate", 0.0),
            estimated_cost=recipe_dict.get("estimated_cost", 5.0),
            difficulty=recipe_dict.get("difficulty", 2),
            image_url=recipe_dict.get("image_url"),
        )
        db.add(recipe)
        count += 1
    
    await db.flush()
    
    return count


async def get_all_cuisines(db: AsyncSession) -> list[str]:
    """
    Get all unique cuisine tags from recipes.
    
    Useful for populating dropdown filters in the UI.
    
    Returns:
        Sorted list of unique cuisine tags
    """
    query = select(Recipe.cuisine_tags)
    result = await db.execute(query)
    
    all_cuisines = set()
    for (tags,) in result.all():
        if tags:
            all_cuisines.update(tags)
    
    return sorted(all_cuisines)


async def get_all_diets(db: AsyncSession) -> list[str]:
    """
    Get all unique diet tags from recipes.
    
    Useful for populating dropdown filters in the UI.
    
    Returns:
        Sorted list of unique diet tags
    """
    query = select(Recipe.diet_tags)
    result = await db.execute(query)
    
    all_diets = set()
    for (tags,) in result.all():
        if tags:
            all_diets.update(tags)
    
    return sorted(all_diets)
