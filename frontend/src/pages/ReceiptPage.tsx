/**
 * ReceiptPage - Receipt ingestion and spending analytics
 * 
 * Features:
 * - Upload CSV receipts
 * - Preview and confirm items
 * - View spending analytics
 * - Recent receipt history
 */

import { useState, useEffect, useCallback } from 'react'
import { Upload, BarChart3, History, CheckCircle } from 'lucide-react'
import { receiptApi } from '../api/receipt'
import type { 
  CSVParseResponse, 
  SpendBreakdownResponse,
  ReceiptSummary,
  ReceiptItemCreate,
} from '../types/receipt'
import ReceiptUploadForm from '../components/ReceiptUploadForm'
import ReceiptPreviewTable from '../components/ReceiptPreviewTable'
import SpendSummary from '../components/SpendSummary'

type Tab = 'upload' | 'analytics' | 'history'
type UploadState = 'form' | 'preview' | 'success'

export default function ReceiptPage() {
  const [activeTab, setActiveTab] = useState<Tab>('upload')
  const [uploadState, setUploadState] = useState<UploadState>('form')
  
  const [isUploading, setIsUploading] = useState(false)
  const [isConfirming, setIsConfirming] = useState(false)
  const [previewData, setPreviewData] = useState<CSVParseResponse | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  
  const [analytics, setAnalytics] = useState<SpendBreakdownResponse | null>(null)
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false)
  
  const [recentReceipts, setRecentReceipts] = useState<ReceiptSummary[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  
  const [error, setError] = useState<string | null>(null)

  const fetchAnalytics = useCallback(async () => {
    setIsLoadingAnalytics(true)
    setError(null)
    try {
      const data = await receiptApi.getSpendBreakdown()
      setAnalytics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics')
    } finally {
      setIsLoadingAnalytics(false)
    }
  }, [])

  const fetchHistory = useCallback(async () => {
    setIsLoadingHistory(true)
    setError(null)
    try {
      const data = await receiptApi.getRecentReceipts(20)
      setRecentReceipts(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history')
    } finally {
      setIsLoadingHistory(false)
    }
  }, [])

  useEffect(() => {
    if (activeTab === 'analytics') {
      fetchAnalytics()
    } else if (activeTab === 'history') {
      fetchHistory()
    }
  }, [activeTab, fetchAnalytics, fetchHistory])

  const handleUpload = async (file: File, store: string, date: Date) => {
    setIsUploading(true)
    setError(null)
    try {
      const response = await receiptApi.uploadCSV(file, store, date)
      setPreviewData(response)
      setUploadState('preview')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const handleConfirm = async () => {
    if (!previewData) return
    
    setIsConfirming(true)
    setError(null)
    try {
      const items: ReceiptItemCreate[] = previewData.items.map(item => ({
        raw_name: item.raw_name,
        quantity: item.quantity,
        unit: item.unit,
        unit_price: item.unit_price,
        category: item.category,
      }))
      
      const response = await receiptApi.confirmReceipt({
        batch_id: previewData.batch_id,
        store: previewData.store,
        purchase_date: previewData.purchase_date,
        items,
        update_pantry: true,
      })
      
      setSuccessMessage(response.message)
      setUploadState('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save receipt')
    } finally {
      setIsConfirming(false)
    }
  }

  const handleCancel = () => {
    setPreviewData(null)
    setUploadState('form')
    setError(null)
  }

  const handleNewUpload = () => {
    setPreviewData(null)
    setSuccessMessage(null)
    setUploadState('form')
    setError(null)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const formatPrice = (price: number) => `$${price.toFixed(2)}`

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Receipts & Analytics</h1>
        <p className="text-gray-600 mt-1">
          Upload receipts to track spending and update your pantry
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        <TabButton
          active={activeTab === 'upload'}
          onClick={() => setActiveTab('upload')}
          icon={<Upload className="w-4 h-4" />}
          label="Upload"
        />
        <TabButton
          active={activeTab === 'analytics'}
          onClick={() => setActiveTab('analytics')}
          icon={<BarChart3 className="w-4 h-4" />}
          label="Analytics"
        />
        <TabButton
          active={activeTab === 'history'}
          onClick={() => setActiveTab('history')}
          icon={<History className="w-4 h-4" />}
          label="History"
        />
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'upload' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          {uploadState === 'form' && (
            <ReceiptUploadForm
              onUpload={handleUpload}
              isLoading={isUploading}
            />
          )}
          
          {uploadState === 'preview' && previewData && (
            <ReceiptPreviewTable
              items={previewData.items}
              store={previewData.store}
              purchaseDate={previewData.purchase_date}
              totalAmount={previewData.total_amount}
              matchedCount={previewData.matched_count}
              newCount={previewData.new_count}
              onConfirm={handleConfirm}
              onCancel={handleCancel}
              isConfirming={isConfirming}
            />
          )}
          
          {uploadState === 'success' && (
            <div className="text-center py-12">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Receipt Saved!
              </h2>
              <p className="text-gray-600 mb-6">{successMessage}</p>
              <div className="flex gap-4 justify-center">
                <button
                  onClick={handleNewUpload}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Upload Another
                </button>
                <button
                  onClick={() => setActiveTab('analytics')}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  View Analytics
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'analytics' && (
        <div>
          {isLoadingAnalytics ? (
            <div className="text-center py-12">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Loading analytics...</p>
            </div>
          ) : analytics ? (
            <SpendSummary data={analytics} />
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Analytics Yet</h3>
              <p className="text-gray-600 mb-4">
                Upload your first receipt to start tracking spending
              </p>
              <button
                onClick={() => setActiveTab('upload')}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Upload Receipt
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          {isLoadingHistory ? (
            <div className="text-center py-12">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Loading history...</p>
            </div>
          ) : recentReceipts.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Store
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Items
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {recentReceipts.map((receipt) => (
                    <tr key={receipt.batch_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">
                        {receipt.store}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {formatDate(receipt.purchase_date)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 text-right">
                        {receipt.item_count}
                      </td>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900 text-right">
                        {formatPrice(receipt.total_amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <History className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Receipt History</h3>
              <p className="text-gray-600 mb-4">
                Your uploaded receipts will appear here
              </p>
              <button
                onClick={() => setActiveTab('upload')}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Upload Receipt
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
}) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors
        ${active
          ? 'bg-white text-gray-900 shadow-sm'
          : 'text-gray-600 hover:text-gray-900'
        }
      `}
    >
      {icon}
      {label}
    </button>
  )
}
