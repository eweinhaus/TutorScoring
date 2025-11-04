import React from 'react'
import { getRiskColor } from '../../utils/formatters'
import { RISK_THRESHOLD } from '../../utils/constants'

/**
 * Risk badge component that displays risk level with color coding
 * @param {number} rate - Reschedule rate percentage
 * @param {number} threshold - Risk threshold (default: 15)
 * @param {string} size - Badge size (small, medium, large)
 */
function RiskBadge({ rate, threshold = RISK_THRESHOLD, size = 'medium' }) {
  const color = getRiskColor(rate, threshold)
  
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

  // Determine risk level text
  let riskText = 'Low Risk'
  if (rate !== null && rate !== undefined && !isNaN(rate)) {
    const value = parseFloat(rate)
    if (value >= threshold) {
      riskText = 'High Risk'
    } else if (value >= threshold * 0.67) {
      riskText = 'Warning'
    } else {
      riskText = 'Low Risk'
    }
  }

  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium ${sizeClasses[size]} ${colorClasses[color]}`}
      title={`Reschedule rate: ${rate !== null && rate !== undefined ? `${rate.toFixed(1)}%` : 'N/A'}`}
    >
      {riskText}
    </span>
  )
}

export default RiskBadge

