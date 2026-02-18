/**
 * SpendSummary - Displays spending analytics
 * Uses CSS bars for simple visualization (no chart library needed)
 */

import { DollarSign, ShoppingBag, Receipt, TrendingUp } from 'lucide-react'
import type { SpendBreakdownResponse } from '../types/receipt'
import { CATEGORY_COLORS } from '../types/receipt'
import { CATEGORY_LABELS, type ItemCategory } from '../types/pantry'

interface SpendSummaryProps {
  data: SpendBreakdownResponse
}

export default function SpendSummary({ data }: SpendSummaryProps) {
  const formatPrice = (price: number) => `$${price.toFixed(2)}`
  
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          icon={<DollarSign className="w-6 h-6" />}
          label="Total Spent"
          value={formatPrice(data.total_spent)}
          color="bg-green-100 text-green-600"
        />
        <StatCard
          icon={<ShoppingBag className="w-6 h-6" />}
          label="Total Items"
          value={data.total_items.toString()}
          color="bg-blue-100 text-blue-600"
        />
        <StatCard
          icon={<Receipt className="w-6 h-6" />}
          label="Receipts"
          value={data.total_receipts.toString()}
          color="bg-purple-100 text-purple-600"
        />
        <StatCard
          icon={<TrendingUp className="w-6 h-6" />}
          label="Date Range"
          value={`${formatDate(data.date_range_start)} - ${formatDate(data.date_range_end)}`}
          valueSize="text-sm"
          color="bg-orange-100 text-orange-600"
        />
      </div>

      {/* Category Breakdown */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Spending by Category</h3>
        {data.by_category.length > 0 ? (
          <div className="space-y-3">
            {data.by_category.map((cat) => (
              <BarRow
                key={cat.category}
                label={CATEGORY_LABELS[cat.category as ItemCategory] || cat.category}
                value={formatPrice(cat.total_spent)}
                percentage={cat.percentage}
                color={CATEGORY_COLORS[cat.category as ItemCategory] || '#6b7280'}
                subtext={`${cat.item_count} items`}
              />
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No spending data yet</p>
        )}
      </div>

      {/* Store Breakdown */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Spending by Store</h3>
        {data.by_store.length > 0 ? (
          <div className="space-y-3">
            {data.by_store.map((store, idx) => (
              <BarRow
                key={store.store}
                label={store.store}
                value={formatPrice(store.total_spent)}
                percentage={store.percentage}
                color={STORE_COLORS[idx % STORE_COLORS.length]}
                subtext={`${store.visit_count} visit${store.visit_count !== 1 ? 's' : ''}`}
              />
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No store data yet</p>
        )}
      </div>

      {/* Monthly Trend */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Spending</h3>
        {data.by_month.length > 0 ? (
          <div className="flex items-end gap-2 h-40">
            {data.by_month.map((month) => {
              const maxSpend = Math.max(...data.by_month.map(m => m.total_spent))
              const heightPercent = maxSpend > 0 ? (month.total_spent / maxSpend) * 100 : 0
              
              return (
                <div key={month.month} className="flex-1 flex flex-col items-center">
                  <span className="text-xs text-gray-600 mb-1">
                    {formatPrice(month.total_spent)}
                  </span>
                  <div
                    className="w-full bg-blue-500 rounded-t transition-all duration-300"
                    style={{ height: `${Math.max(heightPercent, 5)}%` }}
                  />
                  <span className="text-xs text-gray-500 mt-2">
                    {formatMonth(month.month)}
                  </span>
                </div>
              )
            })}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No monthly data yet</p>
        )}
      </div>

      {/* Top Items */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Items by Spending</h3>
        {data.top_items.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs text-gray-500 uppercase border-b">
                  <th className="pb-2">Item</th>
                  <th className="pb-2 text-right">Total Spent</th>
                  <th className="pb-2 text-right">Purchases</th>
                  <th className="pb-2 text-right">Avg Price</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.top_items.map((item, idx) => (
                  <tr key={idx} className="text-sm">
                    <td className="py-2 font-medium text-gray-900 capitalize">
                      {item.name}
                    </td>
                    <td className="py-2 text-right text-gray-900">
                      {formatPrice(item.total_spent)}
                    </td>
                    <td className="py-2 text-right text-gray-600">
                      {item.purchase_count}x
                    </td>
                    <td className="py-2 text-right text-gray-600">
                      {formatPrice(item.avg_price)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">No item data yet</p>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// Helper Components
// =============================================================================

function StatCard({
  icon,
  label,
  value,
  valueSize = 'text-2xl',
  color,
}: {
  icon: React.ReactNode
  label: string
  value: string
  valueSize?: string
  color: string
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${color}`}>{icon}</div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className={`font-bold text-gray-900 ${valueSize}`}>{value}</p>
        </div>
      </div>
    </div>
  )
}

function BarRow({
  label,
  value,
  percentage,
  color,
  subtext,
}: {
  label: string
  value: string
  percentage: number
  color: string
  subtext: string
}) {
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <div className="text-right">
          <span className="text-sm font-semibold text-gray-900">{value}</span>
          <span className="text-xs text-gray-500 ml-2">({percentage.toFixed(1)}%)</span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${percentage}%`, backgroundColor: color }}
          />
        </div>
        <span className="text-xs text-gray-500 w-20 text-right">{subtext}</span>
      </div>
    </div>
  )
}

function formatMonth(monthStr: string): string {
  const [year, month] = monthStr.split('-')
  const date = new Date(parseInt(year), parseInt(month) - 1)
  return date.toLocaleDateString('en-US', { month: 'short' })
}

const STORE_COLORS = [
  '#3b82f6', // blue
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#84cc16', // lime
]
