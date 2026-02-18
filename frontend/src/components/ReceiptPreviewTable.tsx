/**
 * ReceiptPreviewTable - Shows parsed receipt items for review
 */

import { Check, Plus, AlertCircle } from 'lucide-react'
import type { ReceiptItemPreview } from '../types/receipt'
import { CATEGORY_LABELS } from '../types/pantry'

interface ReceiptPreviewTableProps {
  items: ReceiptItemPreview[]
  store: string
  purchaseDate: string
  totalAmount: number
  matchedCount: number
  newCount: number
  onConfirm: () => void
  onCancel: () => void
  isConfirming: boolean
}

export default function ReceiptPreviewTable({
  items,
  store,
  purchaseDate,
  totalAmount,
  matchedCount,
  newCount,
  onConfirm,
  onCancel,
  isConfirming,
}: ReceiptPreviewTableProps) {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`
  }

  const getMatchBadge = (item: ReceiptItemPreview) => {
    if (item.pantry_match_id) {
      const confidence = item.match_score ? Math.round(item.match_score * 100) : 100
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <Check className="w-3 h-3" />
          Matched ({confidence}%)
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
        <Plus className="w-3 h-3" />
        New Item
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex flex-wrap gap-6 justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{store}</h3>
            <p className="text-sm text-gray-500">{formatDate(purchaseDate)}</p>
          </div>
          
          <div className="flex gap-6 text-center">
            <div>
              <p className="text-2xl font-bold text-gray-900">{items.length}</p>
              <p className="text-xs text-gray-500">Items</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">{matchedCount}</p>
              <p className="text-xs text-gray-500">Matched</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600">{newCount}</p>
              <p className="text-xs text-gray-500">New</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{formatPrice(totalAmount)}</p>
              <p className="text-xs text-gray-500">Total</p>
            </div>
          </div>
        </div>
      </div>

      {/* Items Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Item
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Qty
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Unit Price
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Pantry Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {items.map((item, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium text-gray-900">{item.raw_name}</p>
                      <p className="text-xs text-gray-500">→ {item.normalized_name}</p>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700">
                      {CATEGORY_LABELS[item.category] || item.category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900">
                    {item.quantity} {item.unit}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900">
                    {formatPrice(item.unit_price)}
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-gray-900">
                    {formatPrice(item.total_price)}
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      {getMatchBadge(item)}
                      {item.pantry_match_name && (
                        <p className="text-xs text-gray-500 mt-1">
                          → {item.pantry_match_name}
                        </p>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Info Banner */}
      <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-800">
          <p className="font-medium">What happens when you confirm:</p>
          <ul className="mt-1 list-disc list-inside text-blue-700">
            <li>{matchedCount} existing pantry items will have quantities increased</li>
            <li>{newCount} new items will be added to your pantry</li>
            <li>Price history will be saved for analytics</li>
          </ul>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 justify-end">
        <button
          onClick={onCancel}
          disabled={isConfirming}
          className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          disabled={isConfirming}
          className={`
            px-6 py-2 rounded-lg font-medium text-white transition-colors
            ${isConfirming
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-green-600 hover:bg-green-700'
            }
          `}
        >
          {isConfirming ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Saving...
            </span>
          ) : (
            `Confirm & Update Pantry`
          )}
        </button>
      </div>
    </div>
  )
}
