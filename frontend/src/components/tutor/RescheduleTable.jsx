import React, { useState, useMemo } from 'react'
import { formatDateTime, formatHours } from '../../utils/formatters'

/**
 * Reschedule table component for displaying reschedule events
 * @param {Array} reschedules - Array of reschedule event objects
 * @param {boolean} sortable - Enable column sorting
 */
function RescheduleTable({ reschedules = [], sortable = true }) {
  const [sortConfig, setSortConfig] = useState({
    key: 'original_time',
    direction: 'desc',
  })

  const handleSort = (key) => {
    if (!sortable) return

    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }))
  }

  const sortedReschedules = useMemo(() => {
    if (!sortable || !reschedules.length) return reschedules

    return [...reschedules].sort((a, b) => {
      let aValue = a[sortConfig.key]
      let bValue = b[sortConfig.key]

      // Handle date comparisons
      if (sortConfig.key.includes('time') || sortConfig.key.includes('date')) {
        aValue = new Date(aValue)
        bValue = new Date(bValue)
      }

      // Handle null/undefined
      if (aValue == null) return 1
      if (bValue == null) return -1

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1
      }
      return 0
    })
  }, [reschedules, sortConfig, sortable])

  const SortIcon = ({ columnKey }) => {
    if (!sortable || sortConfig.key !== columnKey) {
      return null
    }
    return (
      <span className="ml-1">
        {sortConfig.direction === 'asc' ? '↑' : '↓'}
      </span>
    )
  }

  if (!reschedules || reschedules.length === 0) {
    return (
      <div className="card">
        <p className="text-center text-gray-500 py-8">No reschedules found</p>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th
                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                  sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                }`}
                onClick={() => handleSort('original_time')}
              >
                Date
                <SortIcon columnKey="original_time" />
              </th>
              <th
                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                  sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                }`}
                onClick={() => handleSort('original_time')}
              >
                Original Time
                <SortIcon columnKey="original_time" />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                New Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Reason
              </th>
              <th
                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                  sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                }`}
                onClick={() => handleSort('hours_before_session')}
              >
                Hours Before
                <SortIcon columnKey="hours_before_session" />
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedReschedules.map((reschedule) => (
              <tr key={reschedule.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatDateTime(reschedule.original_time)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatDateTime(reschedule.original_time)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatDateTime(reschedule.new_time)}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900">
                  <div className="max-w-xs truncate" title={reschedule.reason}>
                    {reschedule.reason || 'N/A'}
                  </div>
                  {reschedule.reason_code && (
                    <div className="text-xs text-gray-500">
                      {reschedule.reason_code}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatHours(reschedule.hours_before_session)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default RescheduleTable

