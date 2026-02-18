"""
Pydantic schemas for Meal Planner API.

These schemas define the API contracts for meal plan generation:
- PlanRequest: User preferences and constraints
- PlanResponse: Generated 7-day meal plan with shopping list
"""

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.recipe import RecipeSummary


# =============================================================================
# Request Schema (POST /plan/generate)
# =============================================================================

class PlanRequest(BaseModel):
    """
    Input parameters for generating a meal plan.
    
    All fields are optional with sensible defaults, allowing users
    to generate a plan with minimal input.
    """
    # Budget constraint
    budget: Optional[float] = Field(
        default=None,
        ge=0,
        description="Maximum weekly budget in dollars. If not set, no budget limit.",
        examples=[50.0, 100.0, 150.0]
    )
    
    # Time constraint
    max_time: Optional[int] = Field(
        default=60,
        ge=10,
        le=240,
        description="Maximum cooking time per meal in minutes",
        examples=[30, 45, 60]
    )
    
    # Nutritional goals
    protein_goal: Optional[float] = Field(
        default=None,
        ge=0,
        description="Target protein per meal in grams. Used for scoring, not strict filtering.",
        examples=[30.0, 40.0, 50.0]
    )
    
    # Dietary preferences
    diet_tags: Optional[list[str]] = Field(
        default=None,
        description="Required dietary tags (e.g., 'vegetarian', 'gluten-free'). Recipes must have ALL tags.",
        examples=[["vegetarian"], ["high-protein", "gluten-free"]]
    )
    
    # Cuisine preferences
    cuisine_preferences: Optional[list[str]] = Field(
        default=None,
        description="Preferred cuisines (e.g., 'italian', 'mexican'). Used for scoring, not strict filtering.",
        examples=[["italian", "asian"], ["mexican", "mediterranean"]]
    )
    
    # Variety settings
    servings_per_day: int = Field(
        default=1,
        ge=1,
        le=3,
        description="Number of meals to plan per day (1-3)",
        examples=[1, 2]
    )


# =============================================================================
# Response Schemas
# =============================================================================

class MealPlanDay(BaseModel):
    """
    A single day in the meal plan.
    
    Contains the day number and assigned recipe(s).
    """
    day: int = Field(
        ...,
        ge=1,
        le=7,
        description="Day number (1-7, Monday-Sunday)"
    )
    day_name: str = Field(
        ...,
        description="Day name for display",
        examples=["Monday", "Tuesday"]
    )
    recipes: list[RecipeSummary] = Field(
        ...,
        description="Recipe(s) assigned to this day"
    )
    total_time: int = Field(
        ...,
        ge=0,
        description="Total cooking time for the day in minutes"
    )
    total_protein: float = Field(
        ...,
        ge=0,
        description="Total protein for the day in grams"
    )
    total_calories: float = Field(
        ...,
        ge=0,
        description="Total calories for the day"
    )
    total_cost: float = Field(
        ...,
        ge=0,
        description="Total cost for the day"
    )


class AggregatedIngredient(BaseModel):
    """
    An ingredient aggregated across all recipes in the plan.
    
    Combines quantities for the same ingredient from different recipes
    to create a consolidated shopping list.
    """
    name: str = Field(
        ...,
        description="Ingredient name"
    )
    total_quantity: float = Field(
        ...,
        ge=0,
        description="Total quantity needed across all recipes"
    )
    unit: str = Field(
        ...,
        description="Unit of measurement"
    )
    category: Optional[str] = Field(
        default=None,
        description="Grocery category for shopping organization"
    )


class PlanSummary(BaseModel):
    """
    Summary statistics for the entire meal plan.
    """
    total_recipes: int = Field(
        ...,
        description="Number of unique recipes in the plan"
    )
    total_cost: float = Field(
        ...,
        ge=0,
        description="Estimated total cost for the week"
    )
    total_protein: float = Field(
        ...,
        ge=0,
        description="Total protein for the week in grams"
    )
    total_calories: float = Field(
        ...,
        ge=0,
        description="Total calories for the week"
    )
    avg_time_per_meal: float = Field(
        ...,
        ge=0,
        description="Average cooking time per meal in minutes"
    )
    avg_protein_per_meal: float = Field(
        ...,
        ge=0,
        description="Average protein per meal in grams"
    )


class PlanResponse(BaseModel):
    """
    Complete meal plan response.
    
    Contains the 7-day plan, aggregated shopping list, and summary statistics.
    """
    days: list[MealPlanDay] = Field(
        ...,
        min_length=7,
        max_length=7,
        description="7-day meal plan (Monday-Sunday)"
    )
    shopping_list: list[AggregatedIngredient] = Field(
        ...,
        description="Aggregated ingredients for shopping"
    )
    summary: PlanSummary = Field(
        ...,
        description="Plan summary statistics"
    )
