"""
Recipe model - represents recipes available for meal planning.

This model stores recipe data including ingredients, steps, nutritional
estimates, and tags for filtering during meal plan generation.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Recipe(Base):
    """
    Represents a single recipe for meal planning.
    
    Design decisions:
    - `ingredients` as JSON: Stores [{name, quantity, unit, category}] for flexibility.
      Avoids complex joins while still supporting ingredient-based matching.
    - `steps` as JSON: Ordered list of instruction strings.
    - `cuisine_tags` / `diet_tags` as JSON: Multiple tags without join tables.
    - Nutritional values are per-serving estimates for easy scaling.
    - `estimated_cost` is per-serving to help with budget calculations.
    """
    
    __tablename__ = "recipes"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Basic info
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Serving and time
    servings: Mapped[int] = mapped_column(Integer, default=4)
    time_minutes: Mapped[int] = mapped_column(Integer, default=30)
    
    # Ingredients stored as JSON list:
    # [{"name": "chicken breast", "quantity": 500, "unit": "g", "category": "meat"}, ...]
    ingredients: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    
    # Cooking steps stored as JSON list:
    # ["Preheat oven to 375°F", "Season the chicken...", ...]
    steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    
    # Tags for filtering (stored as JSON arrays)
    # cuisine_tags: ["italian", "mediterranean", "quick"]
    # diet_tags: ["vegetarian", "gluten-free", "high-protein"]
    cuisine_tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    diet_tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    
    # Nutritional estimates (per serving)
    protein_estimate: Mapped[float] = mapped_column(Float, default=0.0)
    calorie_estimate: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Cost estimate per serving (for budget planning)
    estimated_cost: Mapped[float] = mapped_column(Float, default=5.0)
    
    # Difficulty level: 1 (easy) to 5 (advanced)
    difficulty: Mapped[int] = mapped_column(Integer, default=2)
    
    # Image URL (optional, for future UI enhancement)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Recipe(id={self.id}, title='{self.title}', servings={self.servings})>"
