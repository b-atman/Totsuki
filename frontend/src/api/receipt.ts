/**
 * Receipt API client
 * Type-safe functions for receipt ingestion and analytics
 */

import type {
  CSVParseResponse,
  ReceiptConfirmRequest,
  ReceiptIngestionResponse,
  ReceiptItem,
  ReceiptSummary,
  SpendBreakdownResponse,
} from '../types/receipt'

const API_BASE = '/api/v1'

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

export const receiptApi = {
  /**
   * Upload a CSV file and get a preview of parsed items
   */
  async uploadCSV(
    file: File,
    store: string,
    purchaseDate: Date
  ): Promise<CSVParseResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('store', store)
    formData.append('purchase_date', purchaseDate.toISOString())

    const response = await fetch(`${API_BASE}/ingest-receipt`, {
      method: 'POST',
      body: formData,
    })
    return handleResponse<CSVParseResponse>(response)
  },

  /**
   * Confirm a receipt and save to database
   */
  async confirmReceipt(data: ReceiptConfirmRequest): Promise<ReceiptIngestionResponse> {
    const response = await fetch(`${API_BASE}/ingest-receipt/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return handleResponse<ReceiptIngestionResponse>(response)
  },

  /**
   * Get spending analytics breakdown
   */
  async getSpendBreakdown(params?: {
    startDate?: Date
    endDate?: Date
  }): Promise<SpendBreakdownResponse> {
    const searchParams = new URLSearchParams()
    if (params?.startDate) {
      searchParams.set('start_date', params.startDate.toISOString())
    }
    if (params?.endDate) {
      searchParams.set('end_date', params.endDate.toISOString())
    }

    const query = searchParams.toString()
    const url = query
      ? `${API_BASE}/analytics/spend-breakdown?${query}`
      : `${API_BASE}/analytics/spend-breakdown`

    const response = await fetch(url)
    return handleResponse<SpendBreakdownResponse>(response)
  },

  /**
   * Get list of recent receipt uploads
   */
  async getRecentReceipts(limit: number = 10): Promise<ReceiptSummary[]> {
    const response = await fetch(`${API_BASE}/receipts?limit=${limit}`)
    return handleResponse<ReceiptSummary[]>(response)
  },

  /**
   * Get details of a specific receipt batch
   */
  async getReceiptDetails(batchId: string): Promise<ReceiptItem[]> {
    const response = await fetch(`${API_BASE}/receipts/${batchId}`)
    return handleResponse<ReceiptItem[]>(response)
  },

  /**
   * Delete a receipt batch
   */
  async deleteReceipt(batchId: string): Promise<{ message: string; batch_id: string }> {
    const response = await fetch(`${API_BASE}/receipts/${batchId}`, {
      method: 'DELETE',
    })
    return handleResponse<{ message: string; batch_id: string }>(response)
  },
}
