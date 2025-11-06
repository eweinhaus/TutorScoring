import React from 'react'

/**
 * Stats card component for displaying summary statistics
 * @param {string} label - Stat label
 * @param {number|string} value - Stat value
 * @param {string} icon - Icon name (users, alert-triangle, trending-up, percentage)
 * @param {Object} trend - Optional trend data { direction: 'up'|'down', percentage: number }
 * @param {string} color - Optional color scheme (primary, success, warning, danger)
 */
function StatsCard({ label, value, icon, trend, color = 'primary' }) {
  const colorConfig = {
    primary: {
      iconBg: 'bg-blue-500',
      border: 'border-blue-100',
    },
    success: {
      iconBg: 'bg-green-500',
      border: 'border-green-100',
    },
    warning: {
      iconBg: 'bg-orange-500',
      border: 'border-orange-100',
    },
    danger: {
      iconBg: 'bg-red-500',
      border: 'border-red-100',
    },
  }

  const colors = colorConfig[color]

  const renderIcon = () => {
    const iconClass = 'w-5 h-5 text-white'
    
    switch (icon) {
      case 'users':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        )
      case 'alert-triangle':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        )
      case 'trending-up':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        )
      case 'percentage':
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        )
      default:
        return (
          <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        )
    }
  }

  return (
    <div className={`bg-white rounded-lg p-4 shadow-sm border ${colors.border} hover:shadow-md transition-shadow duration-200`}>
      <div className="flex items-center gap-3 mb-2">
        {icon && (
          <div className={`${colors.iconBg} rounded-md p-2 shadow-sm flex-shrink-0`}>
            {renderIcon()}
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide truncate">{label}</p>
        </div>
      </div>
      <div className="ml-0">
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {trend && (
          <div className="flex items-center gap-1 mt-1">
            {trend.direction === 'up' ? (
              <svg
                className="w-3 h-3 text-red-500"
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
                className="w-3 h-3 text-green-500"
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
              className={`text-xs font-semibold ${
                trend.direction === 'up' ? 'text-red-600' : 'text-green-600'
              }`}
            >
              {Math.abs(trend.percentage).toFixed(1)}%
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default StatsCard
