import React from 'react'

/**
 * Stats card component for displaying summary statistics
 * @param {string} label - Stat label
 * @param {number|string} value - Stat value
 * @param {Object} trend - Optional trend data { direction: 'up'|'down', percentage: number }
 * @param {string} color - Optional color scheme (primary, success, warning, danger)
 */
function StatsCard({ label, value, trend, color = 'primary' }) {
  const colorClasses = {
    primary: 'border-l-primary bg-primary/5',
    success: 'border-l-success bg-success/5',
    warning: 'border-l-warning bg-warning/5',
    danger: 'border-l-danger bg-danger/5',
  }

  const borderColorClasses = {
    primary: 'border-l-primary',
    success: 'border-l-success',
    warning: 'border-l-warning',
    danger: 'border-l-danger',
  }

  return (
    <div className={`card border-l-4 ${borderColorClasses[color]} ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">{label}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          {trend && (
            <div className="flex items-center mt-2">
              {trend.direction === 'up' ? (
                <svg
                  className="w-4 h-4 text-red-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M5.293 7.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 7.707a1 1 0 01-1.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                <svg
                  className="w-4 h-4 text-green-500"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M14.707 12.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l2.293-2.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
              <span
                className={`ml-1 text-sm font-medium ${
                  trend.direction === 'up' ? 'text-red-600' : 'text-green-600'
                }`}
              >
                {Math.abs(trend.percentage).toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default StatsCard

