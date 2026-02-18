"""
Meal Planning Engine.

This module contains the core logic for generating weekly meal plans:
1. Filter recipes by hard constraints (time, diet)
2. Score recipes by soft preferences (protein, cuisine, cost)
3. Select 7 recipes with variety
4. Aggregate ingredients for shopping list
5. Calculate summary statistics
"""

import random
from collections import defaultdict
from typing import Sequence

from app.models.recipe import Recipe
from app.schemas.planner import (
    PlanRequest,
    PlanResponse,
    MealPlanDay,
    AggregatedIngredient,
    PlanSummary,
)
from app.schemas.recipe import RecipeSummary

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def generate_meal_plan(
    recipes: Sequence[Recipe],
    request: PlanRequest
) -> PlanResponse:
    """
    Generate a 7-day meal plan based on user preferences.
    
    Algorithm:
    1. Filter recipes by hard constraints
    2. Score remaining recipes
    3. Select 7 recipes with variety optimization
    4. Build response with shopping list and stats
    
    Args:
        recipes: All available recipes from database
        request: User preferences and constraints
    
    Returns:
        Complete meal plan with 7 days, shopping list, and summary
    """
    # Step 1: Filter by hard constraints
    filtered = _filter_recipes(recipes, request)
    
    if len(filtered) < 7:
        # Not enough recipes after filtering - relax constraints
        # Fall back to time-only filtering
        filtered = [r for r in recipes if r.time_minutes <= (request.max_time or 240)]
    
    if len(filtered) < 7:
        # Still not enough - use all recipes
        filtered = list(recipes)
    
    # Step 2: Score recipes
    scored = [(recipe, _score_recipe(recipe, request)) for recipe in filtered]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # Step 3: Select 7 recipes with variety
    selected = _select_with_variety(scored, request)
    
    # Step 4: Build the response
    days = _build_days(selected, request.servings_per_day)
    shopping_list = _aggregate_ingredients(selected, request.servings_per_day)
    summary = _calculate_summary(selected, request.servings_per_day)
    
    return PlanResponse(
        days=days,
        shopping_list=shopping_list,
        summary=summary
    )


def _filter_recipes(
    recipes: Sequence[Recipe],
    request: PlanRequest
) -> list[Recipe]:
    """
    Filter recipes by hard constraints.
    
    Hard constraints (must match):
    - max_time: Recipe time must be <= max_time
    - diet_tags: Recipe must have ALL required diet tags
    - budget: Recipe cost must fit within daily budget allocation
    """
    filtered = []
    
    # Calculate daily budget if weekly budget is set
    daily_budget = None
    if request.budget:
        daily_budget = request.budget / 7 / request.servings_per_day
    
    for recipe in recipes:
        # Time constraint
        if request.max_time and recipe.time_minutes > request.max_time:
            continue
        
        # Diet tags constraint (must have ALL required tags)
        if request.diet_tags:
            recipe_tags = set(recipe.diet_tags or [])
            required_tags = set(request.diet_tags)
            if not required_tags.issubset(recipe_tags):
                continue
        
        # Budget constraint (per serving)
        if daily_budget and recipe.estimated_cost > daily_budget:
            continue
        
        filtered.append(recipe)
    
    return filtered


def _score_recipe(recipe: Recipe, request: PlanRequest) -> float:
    """
    Score a recipe based on soft preferences.
    
    Scoring factors (weighted):
    - Protein match: How close to protein goal (if set)
    - Cuisine match: Bonus for preferred cuisines
    - Time efficiency: Bonus for faster recipes
    - Cost efficiency: Bonus for cheaper recipes
    
    Returns:
        Score from 0 to 100
    """
    score = 50.0  # Base score
    
    # Protein match (0-25 points)
    if request.protein_goal:
        protein_diff = abs(recipe.protein_estimate - request.protein_goal)
        # Perfect match = 25 points, 20g off = 0 points
        protein_score = max(0, 25 - (protein_diff * 1.25))
        score += protein_score
    else:
        # No protein goal - give moderate score for having protein
        score += min(15, recipe.protein_estimate / 3)
    
    # Cuisine preference match (0-15 points)
    if request.cuisine_preferences:
        recipe_cuisines = set(recipe.cuisine_tags or [])
        preferred = set(request.cuisine_preferences)
        matches = len(recipe_cuisines & preferred)
        score += matches * 7.5  # Up to 15 points for 2 matches
    
    # Time efficiency (0-10 points)
    # Faster recipes get bonus (under 30 min = max bonus)
    if recipe.time_minutes <= 30:
        score += 10
    elif recipe.time_minutes <= 45:
        score += 7
    elif recipe.time_minutes <= 60:
        score += 4
    
    # Cost efficiency (0-10 points)
    # Cheaper recipes get bonus
    if recipe.estimated_cost <= 3.0:
        score += 10
    elif recipe.estimated_cost <= 4.5:
        score += 7
    elif recipe.estimated_cost <= 6.0:
        score += 4
    
    # Small random factor for variety (0-5 points)
    score += random.uniform(0, 5)
    
    return score


def _select_with_variety(
    scored_recipes: list[tuple[Recipe, float]],
    request: PlanRequest
) -> list[Recipe]:
    """
    Select 7 recipes while promoting variety.
    
    Strategy:
    - Don't repeat the same recipe
    - Try to avoid same cuisine on consecutive days
    - Prefer higher-scored recipes while maintaining variety
    """
    selected: list[Recipe] = []
    used_ids: set[int] = set()
    recent_cuisines: list[set[str]] = []
    
    for recipe, score in scored_recipes:
        if len(selected) >= 7:
            break
        
        # Skip if already selected
        if recipe.id in used_ids:
            continue
        
        # Check cuisine variety (try to avoid same cuisine as previous day)
        recipe_cuisines = set(recipe.cuisine_tags or [])
        if recent_cuisines and recipe_cuisines & recent_cuisines[-1]:
            # Same cuisine as yesterday - skip if we have other options
            remaining = 7 - len(selected)
            available = len([r for r, _ in scored_recipes if r.id not in used_ids])
            if available > remaining * 1.5:
                continue
        
        selected.append(recipe)
        used_ids.add(recipe.id)
        recent_cuisines.append(recipe_cuisines)
    
    # If we don't have 7, fill with remaining top-scored
    if len(selected) < 7:
        for recipe, score in scored_recipes:
            if recipe.id not in used_ids:
                selected.append(recipe)
                used_ids.add(recipe.id)
                if len(selected) >= 7:
                    break
    
    # Shuffle slightly to avoid predictable patterns
    if len(selected) == 7:
        mid = selected[1:6]
        random.shuffle(mid)
        selected = [selected[0]] + mid + [selected[6]]
    
    return selected


def _build_days(
    recipes: list[Recipe],
    servings_per_day: int
) -> list[MealPlanDay]:
    """
    Build the 7-day meal plan structure.
    """
    days = []
    
    for i, recipe in enumerate(recipes):
        day_num = i + 1
        
        # Create recipe summary
        recipe_summary = RecipeSummary(
            id=recipe.id,
            title=recipe.title,
            servings=recipe.servings,
            time_minutes=recipe.time_minutes,
            cuisine_tags=recipe.cuisine_tags or [],
            diet_tags=recipe.diet_tags or [],
            protein_estimate=recipe.protein_estimate,
            calorie_estimate=recipe.calorie_estimate,
            estimated_cost=recipe.estimated_cost,
            difficulty=recipe.difficulty,
            image_url=recipe.image_url
        )
        
        # Calculate totals for the day
        total_time = recipe.time_minutes * servings_per_day
        total_protein = recipe.protein_estimate * servings_per_day
        total_calories = recipe.calorie_estimate * servings_per_day
        total_cost = recipe.estimated_cost * servings_per_day
        
        days.append(MealPlanDay(
            day=day_num,
            day_name=DAY_NAMES[i],
            recipes=[recipe_summary] * servings_per_day,
            total_time=total_time,
            total_protein=total_protein,
            total_calories=total_calories,
            total_cost=total_cost
        ))
    
    return days


def _aggregate_ingredients(
    recipes: list[Recipe],
    servings_per_day: int
) -> list[AggregatedIngredient]:
    """
    Aggregate ingredients across all recipes for shopping list.
    
    Groups by ingredient name and unit, sums quantities.
    """
    # Group by (name, unit)
    aggregated: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"quantity": 0.0, "category": None}
    )
    
    for recipe in recipes:
        # Scale factor: recipe servings to planned servings
        scale = servings_per_day / recipe.servings if recipe.servings > 0 else 1
        
        for ingredient in recipe.ingredients or []:
            name = ingredient.get("name", "").lower().strip()
            unit = ingredient.get("unit", "unit").lower().strip()
            quantity = ingredient.get("quantity", 0) * scale
            category = ingredient.get("category")
            
            key = (name, unit)
            aggregated[key]["quantity"] += quantity
            if category and not aggregated[key]["category"]:
                aggregated[key]["category"] = category
    
    # Convert to list and sort by category then name
    result = []
    for (name, unit), data in aggregated.items():
        result.append(AggregatedIngredient(
            name=name,
            total_quantity=round(data["quantity"], 2),
            unit=unit,
            category=data["category"]
        ))
    
    # Sort by category (None last), then by name
    result.sort(key=lambda x: (x.category or "zzz", x.name))
    
    return result


def _calculate_summary(
    recipes: list[Recipe],
    servings_per_day: int
) -> PlanSummary:
    """
    Calculate summary statistics for the meal plan.
    """
    total_cost = sum(r.estimated_cost * servings_per_day for r in recipes)
    total_protein = sum(r.protein_estimate * servings_per_day for r in recipes)
    total_calories = sum(r.calorie_estimate * servings_per_day for r in recipes)
    total_time = sum(r.time_minutes for r in recipes)
    
    num_meals = len(recipes) * servings_per_day
    
    return PlanSummary(
        total_recipes=len(set(r.id for r in recipes)),
        total_cost=round(total_cost, 2),
        total_protein=round(total_protein, 1),
        total_calories=round(total_calories, 0),
        avg_time_per_meal=round(total_time / len(recipes), 1) if recipes else 0,
        avg_protein_per_meal=round(total_protein / num_meals, 1) if num_meals else 0
    )
