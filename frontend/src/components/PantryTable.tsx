/**
 * PantryTable - Display pantry items in a table with actions
 */

import { useState } from 'react'
import { Pencil, Trash2, MinusCircle } from 'lucide-react'
import type { PantryItem } from '../types/pantry'
import { CATEGORY_LABELS } from '../types/pantry'
import ExpiryBadge from './ExpiryBadge'

interface PantryTableProps {
  items: PantryItem[]
  onEdit: (item: PantryItem) => void
  onDelete: (item: PantryItem) => void
  onConsume: (item: PantryItem, quantity: number) => void
}

export default function PantryTable({ items, onEdit, onDelete, onConsume }: PantryTableProps) {
  const [consumeItemId, setConsumeItemId] = useState<number | null>(null)
  const [consumeQty, setConsumeQty] = useState('')

  const handleConsumeSubmit = (item: PantryItem) => {
    const qty = parseFloat(consumeQty)
    if (!isNaN(qty) && qty > 0) {
      onConsume(item, qty)
    }
    setConsumeItemId(null)
    setConsumeQty('')
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
        <p className="text-gray-500">No items in your pantry yet.</p>
        <p className="text-gray-400 text-sm mt-1">Add your first item to get started!</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Item
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Quantity
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Expiry
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">{item.name}</div>
                  {item.source === 'receipt' && (
                    <span className="text-xs text-gray-400">From receipt</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {consumeItemId === item.id ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        value={consumeQty}
                        onChange={(e) => setConsumeQty(e.target.value)}
                        placeholder="Qty"
                        min="0.01"
                        step="0.01"
                        max={item.quantity}
                        className="w-20 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
                        autoFocus
                      />
                      <button
                        onClick={() => handleConsumeSubmit(item)}
                        className="text-xs text-primary-600 hover:text-primary-700"
                      >
                        Use
                      </button>
                      <button
                        onClick={() => {
                          setConsumeItemId(null)
                          setConsumeQty('')
                        }}
                        className="text-xs text-gray-400 hover:text-gray-600"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <span className="text-gray-700">
                      {item.quantity} {item.unit}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                    {CATEGORY_LABELS[item.category]}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <ExpiryBadge expiryDate={item.estimated_expiry} />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => {
                        setConsumeItemId(item.id)
                        setConsumeQty('')
                      }}
                      className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
                      title="Consume"
                    >
                      <MinusCircle className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => onEdit(item)}
                      className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                      title="Edit"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => onDelete(item)}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
