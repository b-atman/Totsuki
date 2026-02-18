/**
 * ExpiryBadge - Visual indicator for item expiry status
 * 
 * Colors:
 * - Red: Expired
 * - Yellow: Expiring within 3 days
 * - Green: Fresh (more than 3 days)
 * - Gray: No expiry date set
 */

interface ExpiryBadgeProps {
  expiryDate: string | null
}

type ExpiryStatus = 'expired' | 'expiring-soon' | 'fresh' | 'unknown'

function getExpiryStatus(expiryDate: string | null): ExpiryStatus {
  if (!expiryDate) return 'unknown'

  const expiry = new Date(expiryDate)
  const now = new Date()
  const diffDays = Math.ceil((expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays < 0) return 'expired'
  if (diffDays <= 3) return 'expiring-soon'
  return 'fresh'
}

function formatExpiryText(expiryDate: string | null): string {
  if (!expiryDate) return 'No expiry'

  const expiry = new Date(expiryDate)
  const now = new Date()
  const diffDays = Math.ceil((expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays < 0) return `Expired ${Math.abs(diffDays)}d ago`
  if (diffDays === 0) return 'Expires today'
  if (diffDays === 1) return 'Expires tomorrow'
  if (diffDays <= 7) return `${diffDays}d left`
  
  return expiry.toLocaleDateString()
}

const statusStyles: Record<ExpiryStatus, string> = {
  expired: 'bg-red-100 text-red-800 border-red-200',
  'expiring-soon': 'bg-yellow-100 text-yellow-800 border-yellow-200',
  fresh: 'bg-green-100 text-green-800 border-green-200',
  unknown: 'bg-gray-100 text-gray-600 border-gray-200',
}

export default function ExpiryBadge({ expiryDate }: ExpiryBadgeProps) {
  const status = getExpiryStatus(expiryDate)
  const text = formatExpiryText(expiryDate)

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${statusStyles[status]}`}
    >
      {text}
    </span>
  )
}
