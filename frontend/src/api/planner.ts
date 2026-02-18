/**
 * Meal Planner API client
 * Type-safe functions for all planner-related API calls
 */

import type { PlanRequest, PlanResponse } from '../types/planner'

const API_BASE = '/api/v1/plan'

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
  
  return response.json()
}

export const plannerApi = {
  /**
   * Generate a 7-day meal plan based on preferences
   */
  async generatePlan(request: PlanRequest = {}): Promise<PlanResponse> {
    const response = await fetch(`${API_BASE}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    return handleResponse<PlanResponse>(response)
  },

  /**
   * Get all available cuisine tags for filtering
   */
  async getCuisines(): Promise<string[]> {
    const response = await fetch(`${API_BASE}/cuisines`)
    return handleResponse<string[]>(response)
  },

  /**
   * Get all available diet tags for filtering
   */
  async getDiets(): Promise<string[]> {
    const response = await fetch(`${API_BASE}/diets`)
    return handleResponse<string[]>(response)
  },
}

export { ApiError }
