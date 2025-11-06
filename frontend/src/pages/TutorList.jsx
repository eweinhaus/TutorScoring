import React, { useState, useMemo } from 'react'
import { useTutors } from '../hooks/useTutors'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import TutorRow from '../components/tutor/TutorRow'
import { RISK_STATUS, SORT_OPTIONS, SORT_ORDER } from '../utils/constants'

/**
 * Tutor list page with filtering and sorting
 */
function TutorList() {
  const [riskStatus, setRiskStatus] = useState(RISK_STATUS.ALL)
  const [sortBy, setSortBy] = useState(SORT_OPTIONS.NAME)
  const [sortOrder, setSortOrder] = useState(SORT_ORDER.ASC)
  const [searchQuery, setSearchQuery] = useState('')

  // Build filters for API
  const apiFilters = useMemo(() => {
    const filters = {}
    if (riskStatus !== RISK_STATUS.ALL) {
      filters.risk_status = riskStatus
    }
    if (sortBy) {
      filters.sort_by = sortBy
    }
    if (sortOrder) {
      filters.sort_order = sortOrder
    }
    return filters
  }, [riskStatus, sortBy, sortOrder])

  const { data, isLoading, error, refetch } = useTutors(apiFilters)

  // Filter and sort tutors client-side for search
  const filteredAndSortedTutors = useMemo(() => {
    if (!data || !data.tutors) return []

    let tutors = [...data.tutors]

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      tutors = tutors.filter(
        (tutor) =>
          tutor.name?.toLowerCase().includes(query) ||
          tutor.email?.toLowerCase().includes(query)
      )
    }

    // Apply client-side sorting (if needed, or rely on server-side)
    if (sortBy && sortOrder) {
      tutors.sort((a, b) => {
        let aValue, bValue

        switch (sortBy) {
          case SORT_OPTIONS.RESCHEDULE_RATE:
            aValue = a.reschedule_rate_30d || a.tutor_score?.reschedule_rate_30d || 0
            bValue = b.reschedule_rate_30d || b.tutor_score?.reschedule_rate_30d || 0
            break
          case SORT_OPTIONS.TOTAL_SESSIONS:
            aValue = a.total_sessions_30d || a.tutor_score?.total_sessions_30d || 0
            bValue = b.total_sessions_30d || b.tutor_score?.total_sessions_30d || 0
            break
          case SORT_OPTIONS.NAME:
            aValue = a.name || ''
            bValue = b.name || ''
            break
          default:
            return 0
        }

        if (aValue < bValue) {
          return sortOrder === SORT_ORDER.ASC ? -1 : 1
        }
        if (aValue > bValue) {
          return sortOrder === SORT_ORDER.ASC ? 1 : -1
        }
        return 0
      })
    }

    return tutors
  }, [data, searchQuery, sortBy, sortOrder])

  if (isLoading) {
    return <LoadingSpinner message="Loading tutors..." />
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={refetch} />
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Tutor List</h1>
        <p className="text-gray-600">
          View and manage tutor performance metrics
        </p>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Risk Status Filter */}
          <div>
            <label
              htmlFor="risk-status"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Risk Status
            </label>
            <select
              id="risk-status"
              value={riskStatus}
              onChange={(e) => setRiskStatus(e.target.value)}
              className="input"
            >
              <option value={RISK_STATUS.ALL}>All Tutors</option>
              <option value={RISK_STATUS.HIGH}>High Risk</option>
              <option value={RISK_STATUS.LOW}>Low Risk</option>
            </select>
          </div>

          {/* Sort By */}
          <div>
            <label
              htmlFor="sort-by"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Sort By
            </label>
            <select
              id="sort-by"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="input"
            >
              <option value={SORT_OPTIONS.RESCHEDULE_RATE}>
                Reschedule Rate
              </option>
              <option value={SORT_OPTIONS.TOTAL_SESSIONS}>Total Sessions</option>
              <option value={SORT_OPTIONS.NAME}>Name</option>
            </select>
          </div>

          {/* Sort Order */}
          <div>
            <label
              htmlFor="sort-order"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Order
            </label>
            <select
              id="sort-order"
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="input"
            >
              <option value={SORT_ORDER.DESC}>Descending</option>
              <option value={SORT_ORDER.ASC}>Ascending</option>
            </select>
          </div>
        </div>

        {/* Search */}
        <div className="mt-4">
          <label
            htmlFor="search"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Search Tutors
          </label>
          <input
            id="search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name or email..."
            className="input"
          />
        </div>
      </div>

      {/* Tutor Table */}
      {filteredAndSortedTutors.length === 0 ? (
        <div className="card">
          <p className="text-center text-gray-500 py-8">
            {searchQuery
              ? 'No tutors match your search criteria'
              : 'No tutors found'}
          </p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tutor
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reschedule Rate (30d)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Sessions (30d)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Updated
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredAndSortedTutors.map((tutor) => (
                  <TutorRow key={tutor.id} tutor={tutor} />
                ))}
              </tbody>
            </table>
          </div>

          {/* Results count */}
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              Showing {filteredAndSortedTutors.length} of{' '}
              {data?.tutors?.length || 0} tutors
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default TutorList

