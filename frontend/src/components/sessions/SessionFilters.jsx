import React, { memo } from 'react'
import { DAYS_AHEAD_OPTIONS, RESCHEDULE_RISK_LEVELS } from '../../utils/constants'

/**
 * Session filters component
 * @param {Object} filters - Current filter values
 * @param {Function} onFilterChange - Handler for filter changes
 */
function SessionFilters({ filters, onFilterChange }) {
  const handleDaysAheadChange = (e) => {
    onFilterChange({ ...filters, days_ahead: parseInt(e.target.value) })
  }

  const handleRiskLevelChange = (e) => {
    const value = e.target.value === 'all' ? null : e.target.value
    onFilterChange({ ...filters, risk_level: value })
  }

  const handleClearFilters = () => {
    onFilterChange({
      days_ahead: 7,
      risk_level: null,
      tutor_id: null,
    })
  }

  const hasActiveFilters = filters.risk_level || filters.tutor_id

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6">
      <div className="flex flex-wrap gap-4 items-end">
        <div className="flex-1 min-w-[200px]">
          <label htmlFor="days_ahead" className="block text-sm font-medium text-gray-700 mb-1">
            Days Ahead
          </label>
          <select
            id="days_ahead"
            value={filters.days_ahead || 7}
            onChange={handleDaysAheadChange}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm"
          >
            {DAYS_AHEAD_OPTIONS.map((days) => (
              <option key={days} value={days}>
                {days} days
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1 min-w-[200px]">
          <label htmlFor="risk_level" className="block text-sm font-medium text-gray-700 mb-1">
            Risk Level
          </label>
          <select
            id="risk_level"
            value={filters.risk_level || 'all'}
            onChange={handleRiskLevelChange}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm"
          >
            <option value="all">All</option>
            {RESCHEDULE_RISK_LEVELS.map((level) => (
              <option key={level} value={level}>
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {hasActiveFilters && (
          <div>
            <button
              onClick={handleClearFilters}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
            >
              Clear Filters
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default memo(SessionFilters)


