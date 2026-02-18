/**
 * PantryPage - Main pantry inventory dashboard
 * 
 * Features:
 * - List all pantry items
 * - Add new items
 * - Edit existing items
 * - Delete items
 * - Consume (use) items
 * - Filter by category
 */

import { useState, useEffect, useCallback } from 'react'
import { Plus, RefreshCw, Filter } from 'lucide-react'
import { pantryApi } from '../api/pantry'
import type { PantryItem, PantryItemCreate, PantryItemUpdate, ItemCategory } from '../types/pantry'
import { CATEGORIES, CATEGORY_LABELS } from '../types/pantry'
import PantryTable from '../components/PantryTable'
import AddItemModal from '../components/AddItemModal'
import EditItemModal from '../components/EditItemModal'

export default function PantryPage() {
  const [items, setItems] = useState<PantryItem[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [categoryFilter, setCategoryFilter] = useState<ItemCategory | ''>('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [editItem, setEditItem] = useState<PantryItem | null>(null)

  const fetchItems = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await pantryApi.getItems({
        category: categoryFilter || undefined,
      })
      setItems(response.items)
      setTotal(response.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch items')
    } finally {
      setIsLoading(false)
    }
  }, [categoryFilter])

  useEffect(() => {
    fetchItems()
  }, [fetchItems])

  const handleAddItem = async (data: PantryItemCreate) => {
    await pantryApi.createItem(data)
    await fetchItems()
  }

  const handleUpdateItem = async (id: number, data: PantryItemUpdate) => {
    await pantryApi.updateItem(id, data)
    await fetchItems()
  }

  const handleDeleteItem = async (item: PantryItem) => {
    if (!confirm(`Delete "${item.name}"?`)) return
    
    try {
      await pantryApi.deleteItem(item.id)
      await fetchItems()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete item')
    }
  }

  const handleConsumeItem = async (item: PantryItem, quantity: number) => {
    try {
      await pantryApi.consumeItem({ item_id: item.id, quantity })
      await fetchItems()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to consume item')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Pantry Inventory</h1>
          <p className="text-gray-500 mt-1">
            {total} item{total !== 1 ? 's' : ''} in your pantry
          </p>
        </div>

        {/* Actions Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Item
            </button>
            
            <button
              onClick={fetchItems}
              disabled={isLoading}
              className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value as ItemCategory | '')}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">All Categories</option>
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {CATEGORY_LABELS[cat]}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-4 text-red-500 hover:text-red-700 underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Loading State */}
        {isLoading && items.length === 0 ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 text-gray-400 animate-spin mx-auto" />
            <p className="text-gray-500 mt-2">Loading pantry...</p>
          </div>
        ) : (
          <PantryTable
            items={items}
            onEdit={setEditItem}
            onDelete={handleDeleteItem}
            onConsume={handleConsumeItem}
          />
        )}

        {/* Modals */}
        <AddItemModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          onSubmit={handleAddItem}
        />

        <EditItemModal
          item={editItem}
          onClose={() => setEditItem(null)}
          onSubmit={handleUpdateItem}
        />
      </div>
    </div>
  )
}
