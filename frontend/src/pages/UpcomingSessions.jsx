import React, { useState, useMemo } from 'react'
import { useUpcomingSessions } from '../hooks/useUpcomingSessions'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import UpcomingSessionsTable from '../components/sessions/UpcomingSessionsTable'
import SessionFilters from '../components/sessions/SessionFilters'
import { UPCOMING_SESSIONS_SORT_OPTIONS, SORT_ORDER } from '../utils/constants'

/**
 * Upcoming sessions page with reschedule predictions
 */
function UpcomingSessions() {
  const [filters, setFilters] = useState({
    days_ahead: 7,
    risk_level: null,
    tutor_id: null,
  })
  const [sortBy, setSortBy] = useState(UPCOMING_SESSIONS_SORT_OPTIONS.SCHEDULED_TIME)
  const [sortOrder, setSortOrder] = useState(SORT_ORDER.ASC)
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
  })

  // Build query params
  const queryParams = useMemo(() => ({
    ...filters,
    ...pagination,
    sort_by: sortBy,
    sort_order: sortOrder,
  }), [filters, pagination, sortBy, sortOrder])

  const { sessions, total, limit, offset, isLoading, error, refetch } = useUpcomingSessions(queryParams)

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters)
    setPagination({ ...pagination, offset: 0 }) // Reset to first page when filters change
  }

  const handleSort = (field, order) => {
    setSortBy(field)
    setSortOrder(order)
    setPagination({ ...pagination, offset: 0 }) // Reset to first page when sorting changes
  }

  const handlePageChange = (newOffset) => {
    setPagination({ ...pagination, offset: newOffset })
  }

  if (isLoading) {
    return <LoadingSpinner message="Loading upcoming sessions..." />
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={refetch} />
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upcoming Sessions</h1>
        <p className="text-gray-600">
          View upcoming sessions with reschedule probability predictions
        </p>
      </div>

      {/* Filters */}
      <SessionFilters filters={filters} onFilterChange={handleFilterChange} />

      {/* Summary Stats */}
      <div className="mb-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            Showing <span className="font-semibold">{sessions.length}</span> of{' '}
            <span className="font-semibold">{total}</span> upcoming sessions
            {filters.days_ahead && ` (next ${filters.days_ahead} days)`}
          </p>
        </div>
      </div>

      {/* Sessions Table */}
      <div className="card p-0 overflow-hidden">
        <UpcomingSessionsTable
          sessions={sessions}
          onSort={handleSort}
          sortBy={sortBy}
          sortOrder={sortOrder}
        />

        {/* Pagination */}
        {total > limit && (
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Showing {offset + 1} to {Math.min(offset + limit, total)} of {total} sessions
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handlePageChange(Math.max(0, offset - limit))}
                disabled={offset === 0}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
              >
                Previous
              </button>
              <button
                onClick={() => handlePageChange(offset + limit)}
                disabled={offset + limit >= total}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Refresh Button */}
      <div className="mt-4 flex justify-end">
        <button
          onClick={() => refetch()}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
        >
          Refresh
        </button>
      </div>
    </div>
  )
}

export default UpcomingSessions

