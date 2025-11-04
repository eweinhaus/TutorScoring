import React from 'react'
import { RISK_THRESHOLD } from '../../utils/constants'

// Safe color calculation - avoid importing getRiskColor to prevent circular issues
const getSafeRiskColor = (rate, threshold = 15) => {
  if (rate == null || rate === '') return 'gray'
  const value = typeof rate === 'string' ? parseFloat(rate) : Number(rate)
  if (isNaN(value) || !isFinite(value)) return 'gray'
  if (value >= threshold) return 'red'
  if (value >= threshold * 0.67) return 'yellow'
  return 'green'
}

/**
 * Risk badge component that displays risk level with color coding
 * @param {number} rate - Reschedule rate percentage
 * @param {number} threshold - Risk threshold (default: 15)
 * @param {string} size - Badge size (small, medium, large)
 */
function RiskBadge({ rate, threshold = RISK_THRESHOLD, size = 'medium' }) {
  const sizeClasses = {
    small: 'text-xs px-2 py-1',
    medium: 'text-sm px-3 py-1.5',
    large: 'text-base px-4 py-2',
  }

  const colorClasses = {
    red: 'bg-red-100 text-red-800 border-red-300',
    yellow: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    green: 'bg-green-100 text-green-800 border-green-300',
    gray: 'bg-gray-100 text-gray-800 border-gray-300',
  }
  
  // Safely parse rate value - handle all edge cases
  let numericRate = null
  if (rate != null && rate !== '') {
    try {
      const parsed = typeof rate === 'string' ? parseFloat(rate) : Number(rate)
      if (!isNaN(parsed) && isFinite(parsed)) {
        numericRate = parsed
      }
    } catch (e) {
      // Ignore parsing errors
    }
  }
  
  // Get color with safety check - use safe calculation
  let color = 'gray' // Default fallback
  try {
    if (numericRate !== null) {
      const calculatedColor = getSafeRiskColor(numericRate, threshold)
      // Ensure the color exists in colorClasses
      color = colorClasses[calculatedColor] ? calculatedColor : 'gray'
    }
  } catch (error) {
    // Fallback to gray on any error
    color = 'gray'
  }

  // Determine risk level text
  let riskText = 'Low Risk'
  if (numericRate !== null) {
    if (numericRate >= threshold) {
      riskText = 'High Risk'
    } else if (numericRate >= threshold * 0.67) {
      riskText = 'Warning'
    } else {
      riskText = 'Low Risk'
    }
  }

  // Format rate for title
  const rateDisplay = numericRate !== null
    ? `${numericRate.toFixed(1)}%`
    : 'N/A'

  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium ${sizeClasses[size]} ${colorClasses[color]}`}
      title={`Reschedule rate: ${rateDisplay}`}
    >
      {riskText}
    </span>
  )
}

export default RiskBadge

