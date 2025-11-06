import React, { memo } from 'react'
import RiskBadge from '../common/RiskBadge'
import { formatRescheduleProbability, formatDateTime } from '../../utils/formatters'
import { UPCOMING_SESSIONS_SORT_OPTIONS, SORT_ORDER } from '../../utils/constants'

/**
 * Upcoming sessions table component
 * @param {Array} sessions - Array of session objects
 * @param {Function} onSort - Sort handler function
 * @param {string} sortBy - Current sort field
 * @param {string} sortOrder - Current sort order (asc/desc)
 */
function UpcomingSessionsTable({ sessions, onSort, sortBy, sortOrder }) {
  const handleSort = (field) => {
    if (onSort) {
      const newOrder = sortBy === field && sortOrder === 'asc' ? 'desc' : 'asc'
      onSort(field, newOrder)
    }
  }

  const getSortIcon = (field) => {
    if (sortBy !== field) {
      return (
        <span className="text-gray-400 ml-1">
          <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
          </svg>
        </span>
      )
    }
    
    if (sortOrder === 'asc') {
      return (
        <span className="text-primary ml-1">
          <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        </span>
      )
    } else {
      return (
        <span className="text-primary ml-1">
          <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </span>
      )
    }
  }

  if (sessions.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-lg">No upcoming sessions found</p>
        <p className="text-gray-400 text-sm mt-2">Try adjusting your filters</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort(UPCOMING_SESSIONS_SORT_OPTIONS.TUTOR_NAME)}
            >
              <div className="flex items-center">
                Tutor Name
                {getSortIcon(UPCOMING_SESSIONS_SORT_OPTIONS.TUTOR_NAME)}
              </div>
            </th>
            <th
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort(UPCOMING_SESSIONS_SORT_OPTIONS.STUDENT_ID)}
            >
              <div className="flex items-center">
                Student Name
                {getSortIcon(UPCOMING_SESSIONS_SORT_OPTIONS.STUDENT_ID)}
              </div>
            </th>
            <th
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort(UPCOMING_SESSIONS_SORT_OPTIONS.SCHEDULED_TIME)}
            >
              <div className="flex items-center">
                Session Time
                {getSortIcon(UPCOMING_SESSIONS_SORT_OPTIONS.SCHEDULED_TIME)}
              </div>
            </th>
            <th
              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort(UPCOMING_SESSIONS_SORT_OPTIONS.RESCHEDULE_PROBABILITY)}
            >
              <div className="flex items-center">
                Reschedule Probability
                {getSortIcon(UPCOMING_SESSIONS_SORT_OPTIONS.RESCHEDULE_PROBABILITY)}
              </div>
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Risk Level
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sessions.map((session) => {
            // reschedule_probability is 0-1 from API, convert to percentage for display/comparison
            const probabilityPercent = (session.reschedule_probability || 0) * 100
            return (
              <tr key={session.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{session.tutor_name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {session.student_name || session.student_id}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{formatDateTime(session.scheduled_time)}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`text-sm font-semibold ${
                    probabilityPercent >= 35 ? 'text-red-600' :
                    probabilityPercent >= 15 ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>
                    {formatRescheduleProbability(session.reschedule_probability)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <RiskBadge 
                    rate={probabilityPercent} 
                    size="small"
                    threshold={35} // Use higher threshold for reschedule predictions (35% vs 15%)
                  />
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default memo(UpcomingSessionsTable)

