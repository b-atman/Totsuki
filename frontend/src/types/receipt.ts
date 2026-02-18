/**
 * TypeScript types for Receipt Ingestion API
 * These match the Pydantic schemas in the backend
 */

import { ItemCategory } from './pantry'

// =============================================================================
// Receipt Item Types
// =============================================================================

export interface ReceiptItem {
  id: number
  user_id: number
  receipt_batch_id: string
  raw_name: string
  normalized_name: string
  quantity: number
  unit: string
  unit_price: number
  total_price: number
  category: ItemCategory
  store: string
  purchase_date: string
  matched_pantry_item_id: number | null
  created_at: string
}

export interface ReceiptItemPreview {
  raw_name: string
  normalized_name: string
  quantity: number
  unit: string
  unit_price: number
  total_price: number
  category: ItemCategory
  pantry_match_name: string | null
  pantry_match_id: number | null
  match_score: number | null
  will_create_new: boolean
}

export interface ReceiptItemCreate {
  raw_name: string
  quantity?: number
  unit?: string
  unit_price: number
  category?: ItemCategory
}

// =============================================================================
// CSV Upload Types
// =============================================================================

export interface CSVParseResponse {
  batch_id: string
  store: string
  purchase_date: string
  items: ReceiptItemPreview[]
  total_items: number
  total_amount: number
  matched_count: number
  new_count: number
}

export interface ReceiptConfirmRequest {
  batch_id: string
  store: string
  purchase_date: string
  items: ReceiptItemCreate[]
  update_pantry: boolean
}

export interface ReceiptIngestionResponse {
  batch_id: string
  items_created: number
  pantry_items_updated: number
  pantry_items_created: number
  total_amount: number
  message: string
}

// =============================================================================
// Analytics Types
// =============================================================================

export interface SpendByCategory {
  category: string
  total_spent: number
  item_count: number
  percentage: number
}

export interface SpendByStore {
  store: string
  total_spent: number
  visit_count: number
  percentage: number
}

export interface SpendByMonth {
  month: string
  total_spent: number
  item_count: number
}

export interface TopItem {
  name: string
  total_spent: number
  total_quantity: number
  purchase_count: number
  avg_price: number
}

export interface SpendBreakdownResponse {
  total_spent: number
  total_items: number
  total_receipts: number
  date_range_start: string | null
  date_range_end: string | null
  by_category: SpendByCategory[]
  by_store: SpendByStore[]
  by_month: SpendByMonth[]
  top_items: TopItem[]
}

// =============================================================================
// Receipt History Types
// =============================================================================

export interface ReceiptSummary {
  batch_id: string
  store: string
  purchase_date: string
  total_amount: number
  item_count: number
}

// =============================================================================
// Helper Constants
// =============================================================================

export const CATEGORY_COLORS: Record<ItemCategory, string> = {
  produce: '#22c55e',    // green
  dairy: '#3b82f6',      // blue
  meat: '#ef4444',       // red
  seafood: '#06b6d4',    // cyan
  bakery: '#f59e0b',     // amber
  frozen: '#8b5cf6',     // violet
  pantry: '#78716c',     // stone
  beverages: '#14b8a6',  // teal
  snacks: '#f97316',     // orange
  condiments: '#eab308', // yellow
  spices: '#a855f7',     // purple
  other: '#6b7280',      // gray
}
