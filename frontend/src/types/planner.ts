/**
 * TypeScript types for Meal Planner API
 * These match the Pydantic schemas in the backend
 */

// =============================================================================
// Recipe Types
// =============================================================================

export interface IngredientItem {
  name: string
  quantity: number
  unit: string
  category?: string | null
}

export interface RecipeSummary {
  id: number
  title: string
  servings: number
  time_minutes: number
  cuisine_tags: string[]
  diet_tags: string[]
  protein_estimate: number
  calorie_estimate: number
  estimated_cost: number
  difficulty: number
  image_url?: string | null
}

// =============================================================================
// Plan Request Types
// =============================================================================

export interface PlanRequest {
  budget?: number | null
  max_time?: number
  protein_goal?: number | null
  diet_tags?: string[] | null
  cuisine_preferences?: string[] | null
  servings_per_day?: number
}

// =============================================================================
// Plan Response Types
// =============================================================================

export interface MealPlanDay {
  day: number
  day_name: string
  recipes: RecipeSummary[]
  total_time: number
  total_protein: number
  total_calories: number
  total_cost: number
}

export interface AggregatedIngredient {
  name: string
  total_quantity: number
  unit: string
  category?: string | null
}

export interface PlanSummary {
  total_recipes: number
  total_cost: number
  total_protein: number
  total_calories: number
  avg_time_per_meal: number
  avg_protein_per_meal: number
}

export interface PlanResponse {
  days: MealPlanDay[]
  shopping_list: AggregatedIngredient[]
  summary: PlanSummary
}

// =============================================================================
// Helper Constants
// =============================================================================

export const DAY_NAMES = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
] as const

export const DIFFICULTY_LABELS: Record<number, string> = {
  1: 'Easy',
  2: 'Medium',
  3: 'Intermediate',
  4: 'Advanced',
  5: 'Expert',
}

export const DIFFICULTY_COLORS: Record<number, string> = {
  1: 'text-green-600',
  2: 'text-lime-600',
  3: 'text-yellow-600',
  4: 'text-orange-600',
  5: 'text-red-600',
}

// Common cuisine display names
export const CUISINE_LABELS: Record<string, string> = {
  american: 'American',
  argentinian: 'Argentinian',
  asian: 'Asian',
  bbq: 'BBQ',
  brunch: 'Brunch',
  chinese: 'Chinese',
  comfort: 'Comfort Food',
  curry: 'Curry',
  greek: 'Greek',
  hawaiian: 'Hawaiian',
  healthy: 'Healthy',
  indian: 'Indian',
  italian: 'Italian',
  japanese: 'Japanese',
  korean: 'Korean',
  latin: 'Latin',
  mediterranean: 'Mediterranean',
  mexican: 'Mexican',
  'middle-eastern': 'Middle Eastern',
  quick: 'Quick',
  seafood: 'Seafood',
  'tex-mex': 'Tex-Mex',
  thai: 'Thai',
}

// Common diet tag display names
export const DIET_LABELS: Record<string, string> = {
  'gluten-free': 'Gluten-Free',
  'high-fiber': 'High Fiber',
  'high-protein': 'High Protein',
  keto: 'Keto',
  'low-carb': 'Low Carb',
  vegan: 'Vegan',
  vegetarian: 'Vegetarian',
}
