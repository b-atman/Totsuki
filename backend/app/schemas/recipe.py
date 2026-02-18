"""
Pydantic schemas for Recipe API endpoints.

These schemas define the API contracts for recipe data:
- IngredientItem: Structure for each ingredient in a recipe
- RecipeResponse: What the API returns for recipe queries
- RecipeListResponse: For listing multiple recipes
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Nested Schemas (for JSON fields)
# =============================================================================

class IngredientItem(BaseModel):
    """
    Represents a single ingredient in a recipe.
    
    This schema defines the structure stored in the Recipe.ingredients JSON field.
    Includes optional category for grouping in shopping lists.
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Ingredient name",
        examples=["chicken breast", "olive oil", "garlic"]
    )
    quantity: float = Field(
        ...,
        gt=0,
        description="Amount needed",
        examples=[500, 2, 0.5]
    )
    unit: str = Field(
        ...,
        max_length=50,
        description="Unit of measurement",
        examples=["g", "tbsp", "cloves", "cups"]
    )
    category: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Grocery category for shopping list grouping",
        examples=["meat", "produce", "pantry"]
    )


# =============================================================================
# Response Schemas (API output)
# =============================================================================

class RecipeBase(BaseModel):
    """
    Base schema with common recipe fields.
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Recipe title",
        examples=["Grilled Chicken Salad", "Spaghetti Bolognese"]
    )
    description: Optional[str] = Field(
        default=None,
        description="Brief description of the dish",
        examples=["A healthy, protein-packed salad perfect for lunch"]
    )
    servings: int = Field(
        default=4,
        gt=0,
        description="Number of servings the recipe makes",
        examples=[2, 4, 6]
    )
    time_minutes: int = Field(
        default=30,
        gt=0,
        description="Total cooking time in minutes",
        examples=[15, 30, 60]
    )
    ingredients: list[IngredientItem] = Field(
        default_factory=list,
        description="List of ingredients with quantities"
    )
    steps: list[str] = Field(
        default_factory=list,
        description="Ordered cooking instructions",
        examples=[["Preheat oven to 375°F", "Season the chicken", "Bake for 25 minutes"]]
    )
    cuisine_tags: list[str] = Field(
        default_factory=list,
        description="Cuisine style tags",
        examples=[["italian", "mediterranean", "quick"]]
    )
    diet_tags: list[str] = Field(
        default_factory=list,
        description="Dietary tags",
        examples=[["high-protein", "low-carb", "gluten-free"]]
    )
    protein_estimate: float = Field(
        default=0.0,
        ge=0,
        description="Estimated protein per serving (grams)",
        examples=[35.0, 20.0]
    )
    calorie_estimate: float = Field(
        default=0.0,
        ge=0,
        description="Estimated calories per serving",
        examples=[450, 600]
    )
    estimated_cost: float = Field(
        default=5.0,
        ge=0,
        description="Estimated cost per serving ($)",
        examples=[3.50, 5.00]
    )
    difficulty: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Difficulty level (1=easy, 5=advanced)",
        examples=[1, 2, 3]
    )
    image_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL to recipe image"
    )


class RecipeResponse(RecipeBase):
    """
    Schema for recipe API responses.
    
    Includes all base fields plus database-generated fields.
    """
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RecipeSummary(BaseModel):
    """
    Lightweight recipe summary for lists and meal plans.
    
    Excludes steps and full ingredients to reduce payload size.
    """
    id: int
    title: str
    servings: int
    time_minutes: int
    cuisine_tags: list[str]
    diet_tags: list[str]
    protein_estimate: float
    calorie_estimate: float
    estimated_cost: float
    difficulty: int
    image_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class RecipeListResponse(BaseModel):
    """
    Schema for listing recipes with metadata.
    """
    recipes: list[RecipeSummary]
    total: int = Field(description="Total number of recipes")
    
    model_config = ConfigDict(from_attributes=True)
