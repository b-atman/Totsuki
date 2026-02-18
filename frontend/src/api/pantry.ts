/**
 * Pantry API client
 * Type-safe functions for all pantry-related API calls
 */

import type {
  PantryItem,
  PantryItemCreate,
  PantryItemUpdate,
  PantryItemConsume,
  PantryListResponse,
  ItemCategory,
} from '../types/pantry'

const API_BASE = '/api/v1/inventory'

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new ApiError(
      response.status,
      errorData.detail || `HTTP ${response.status}`
    )
  }
  
  if (response.status === 204) {
    return undefined as T
  }
  
  return response.json()
}

export const pantryApi = {
  /**
   * Get all pantry items with optional filtering
   */
  async getItems(params?: {
    category?: ItemCategory
    skip?: number
    limit?: number
  }): Promise<PantryListResponse> {
    const searchParams = new URLSearchParams()
    if (params?.category) searchParams.set('category', params.category)
    if (params?.skip) searchParams.set('skip', params.skip.toString())
    if (params?.limit) searchParams.set('limit', params.limit.toString())

    const query = searchParams.toString()
    const url = query ? `${API_BASE}?${query}` : API_BASE

    const response = await fetch(url)
    return handleResponse<PantryListResponse>(response)
  },

  /**
   * Create a new pantry item
   */
  async createItem(data: PantryItemCreate): Promise<PantryItem> {
    const response = await fetch(`${API_BASE}/item`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return handleResponse<PantryItem>(response)
  },

  /**
   * Update an existing pantry item
   */
  async updateItem(id: number, data: PantryItemUpdate): Promise<PantryItem> {
    const response = await fetch(`${API_BASE}/item/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return handleResponse<PantryItem>(response)
  },

  /**
   * Delete a pantry item
   */
  async deleteItem(id: number): Promise<void> {
    const response = await fetch(`${API_BASE}/item/${id}`, {
      method: 'DELETE',
    })
    return handleResponse<void>(response)
  },

  /**
   * Consume a quantity of an item
   * Returns updated item, or null if item was fully consumed
   */
  async consumeItem(data: PantryItemConsume): Promise<PantryItem | null> {
    const response = await fetch(`${API_BASE}/consume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return handleResponse<PantryItem | null>(response)
  },
}
