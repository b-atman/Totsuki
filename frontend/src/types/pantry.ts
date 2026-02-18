/**
 * TypeScript types for Pantry API
 * These match the Pydantic schemas in the backend
 */

export type ItemCategory =
  | 'produce'
  | 'dairy'
  | 'meat'
  | 'seafood'
  | 'bakery'
  | 'frozen'
  | 'pantry'
  | 'beverages'
  | 'snacks'
  | 'condiments'
  | 'spices'
  | 'other'

export type ItemSource = 'manual' | 'receipt'

export interface PantryItem {
  id: number
  user_id: number
  name: string
  canonical_name: string | null
  quantity: number
  unit: string
  estimated_expiry: string | null
  category: ItemCategory
  source: ItemSource
  created_at: string
  last_updated: string
}

export interface PantryItemCreate {
  name: string
  canonical_name?: string | null
  quantity?: number
  unit?: string
  estimated_expiry?: string | null
  category?: ItemCategory
  source?: ItemSource
}

export interface PantryItemUpdate {
  name?: string
  canonical_name?: string | null
  quantity?: number
  unit?: string
  estimated_expiry?: string | null
  category?: ItemCategory
}

export interface PantryItemConsume {
  item_id: number
  quantity: number
}

export interface PantryListResponse {
  items: PantryItem[]
  total: number
}

export const CATEGORY_LABELS: Record<ItemCategory, string> = {
  produce: 'Produce',
  dairy: 'Dairy',
  meat: 'Meat',
  seafood: 'Seafood',
  bakery: 'Bakery',
  frozen: 'Frozen',
  pantry: 'Pantry',
  beverages: 'Beverages',
  snacks: 'Snacks',
  condiments: 'Condiments',
  spices: 'Spices',
  other: 'Other',
}

export const CATEGORIES: ItemCategory[] = [
  'produce',
  'dairy',
  'meat',
  'seafood',
  'bakery',
  'frozen',
  'pantry',
  'beverages',
  'snacks',
  'condiments',
  'spices',
  'other',
]
