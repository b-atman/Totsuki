/**
 * ReceiptUploadForm - Form to upload CSV receipts
 */

import { useState, useRef } from 'react'
import { Upload, FileText, Calendar, Store } from 'lucide-react'

interface ReceiptUploadFormProps {
  onUpload: (file: File, store: string, date: Date) => Promise<void>
  isLoading: boolean
}

const COMMON_STORES = [
  'Walmart',
  'Kroger',
  'Costco',
  'Target',
  'Safeway',
  'Whole Foods',
  'Trader Joe\'s',
  'Aldi',
  'Other',
]

export default function ReceiptUploadForm({ onUpload, isLoading }: ReceiptUploadFormProps) {
  const [file, setFile] = useState<File | null>(null)
  const [store, setStore] = useState('')
  const [customStore, setCustomStore] = useState('')
  const [purchaseDate, setPurchaseDate] = useState(
    new Date().toISOString().split('T')[0]
  )
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Please select a CSV file')
        return
      }
      setFile(selectedFile)
      setError(null)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      if (!droppedFile.name.endsWith('.csv')) {
        setError('Please drop a CSV file')
        return
      }
      setFile(droppedFile)
      setError(null)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!file) {
      setError('Please select a CSV file')
      return
    }

    const finalStore = store === 'Other' ? customStore.trim() : store
    if (!finalStore) {
      setError('Please enter a store name')
      return
    }

    if (!purchaseDate) {
      setError('Please select a purchase date')
      return
    }

    try {
      await onUpload(file, finalStore, new Date(purchaseDate))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* File Drop Zone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-colors duration-200
          ${dragOver 
            ? 'border-blue-500 bg-blue-50' 
            : file 
              ? 'border-green-500 bg-green-50' 
              : 'border-gray-300 hover:border-gray-400'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="hidden"
        />
        
        {file ? (
          <div className="flex items-center justify-center gap-3">
            <FileText className="w-8 h-8 text-green-600" />
            <div className="text-left">
              <p className="font-medium text-gray-900">{file.name}</p>
              <p className="text-sm text-gray-500">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
        ) : (
          <>
            <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 mb-2">
              <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
            </p>
            <p className="text-sm text-gray-500">CSV files only</p>
          </>
        )}
      </div>

      {/* Store Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Store className="w-4 h-4 inline mr-2" />
          Store
        </label>
        <select
          value={store}
          onChange={(e) => setStore(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select a store...</option>
          {COMMON_STORES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        
        {store === 'Other' && (
          <input
            type="text"
            value={customStore}
            onChange={(e) => setCustomStore(e.target.value)}
            placeholder="Enter store name"
            className="w-full mt-2 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        )}
      </div>

      {/* Purchase Date */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Calendar className="w-4 h-4 inline mr-2" />
          Purchase Date
        </label>
        <input
          type="date"
          value={purchaseDate}
          onChange={(e) => setPurchaseDate(e.target.value)}
          max={new Date().toISOString().split('T')[0]}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading || !file}
        className={`
          w-full py-3 px-4 rounded-lg font-medium text-white
          transition-colors duration-200
          ${isLoading || !file
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700'
          }
        `}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Parsing...
          </span>
        ) : (
          'Upload & Preview'
        )}
      </button>

      {/* CSV Format Help */}
      <div className="text-sm text-gray-500 bg-gray-50 p-4 rounded-lg">
        <p className="font-medium mb-2">Expected CSV format:</p>
        <code className="block bg-gray-100 p-2 rounded text-xs">
          name,quantity,unit,price<br />
          Milk,1,gallon,3.99<br />
          Chicken Breast,2,lb,8.99
        </code>
      </div>
    </form>
  )
}
