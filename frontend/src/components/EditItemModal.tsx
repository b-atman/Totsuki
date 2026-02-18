/**
 * EditItemModal - Form to edit existing pantry items
 */

import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import type { PantryItem, PantryItemUpdate, ItemCategory } from '../types/pantry'
import { CATEGORIES, CATEGORY_LABELS } from '../types/pantry'

interface EditItemModalProps {
  item: PantryItem | null
  onClose: () => void
  onSubmit: (id: number, data: PantryItemUpdate) => Promise<void>
}

const COMMON_UNITS = ['unit', 'lb', 'oz', 'kg', 'g', 'gallon', 'liter', 'cups', 'pieces']

export default function EditItemModal({ item, onClose, onSubmit }: EditItemModalProps) {
  const [name, setName] = useState('')
  const [quantity, setQuantity] = useState('')
  const [unit, setUnit] = useState('')
  const [category, setCategory] = useState<ItemCategory>('other')
  const [expiryDate, setExpiryDate] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (item) {
      setName(item.name)
      setQuantity(item.quantity.toString())
      setUnit(item.unit)
      setCategory(item.category)
      setExpiryDate(
        item.estimated_expiry
          ? new Date(item.estimated_expiry).toISOString().split('T')[0]
          : ''
      )
    }
  }, [item])

  if (!item) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError('Name is required')
      return
    }

    const qty = parseFloat(quantity)
    if (isNaN(qty) || qty <= 0) {
      setError('Quantity must be a positive number')
      return
    }

    setIsSubmitting(true)
    try {
      await onSubmit(item.id, {
        name: name.trim(),
        quantity: qty,
        unit: unit || 'unit',
        category,
        estimated_expiry: expiryDate ? new Date(expiryDate).toISOString() : null,
      })
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update item')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black/50" onClick={onClose} />
        
        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Edit Item</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="edit-name" className="block text-sm font-medium text-gray-700 mb-1">
                Item Name *
              </label>
              <input
                type="text"
                id="edit-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="edit-quantity" className="block text-sm font-medium text-gray-700 mb-1">
                  Quantity
                </label>
                <input
                  type="number"
                  id="edit-quantity"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  min="0.01"
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="edit-unit" className="block text-sm font-medium text-gray-700 mb-1">
                  Unit
                </label>
                <select
                  id="edit-unit"
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {COMMON_UNITS.map((u) => (
                    <option key={u} value={u}>
                      {u}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label htmlFor="edit-category" className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                id="edit-category"
                value={category}
                onChange={(e) => setCategory(e.target.value as ItemCategory)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {CATEGORY_LABELS[cat]}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="edit-expiry" className="block text-sm font-medium text-gray-700 mb-1">
                Expiry Date (optional)
              </label>
              <input
                type="date"
                id="edit-expiry"
                value={expiryDate}
                onChange={(e) => setExpiryDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
