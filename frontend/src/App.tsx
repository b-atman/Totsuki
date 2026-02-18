/**
 * Totsuki - Grocery Optimizer
 * Main App Component with Routing
 */

import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { Package, UtensilsCrossed, Receipt } from 'lucide-react'
import PantryPage from './pages/PantryPage'
import PlanPage from './pages/PlanPage'
import ReceiptPage from './pages/ReceiptPage'

const navItems = [
  { path: '/', label: 'Pantry', icon: Package },
  { path: '/plan', label: 'Meal Plan', icon: UtensilsCrossed },
  { path: '/receipts', label: 'Receipts', icon: Receipt },
]

function Navbar() {
  const location = useLocation()

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">🍳</span>
            <span className="font-bold text-xl text-gray-900">Totsuki</span>
          </Link>

          {/* Nav Links */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <Routes>
        <Route path="/" element={<PantryPage />} />
        <Route path="/plan" element={<PlanPage />} />
        <Route path="/receipts" element={<ReceiptPage />} />
      </Routes>
    </div>
  )
}
