import React, { useState, useMemo, useEffect } from 'react'
import { useTutors } from '../hooks/useTutors'
import { useDebounce } from '../hooks/useDebounce'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import TutorRow from '../components/tutor/TutorRow'
import { RISK_STATUS, SORT_OPTIONS, SORT_ORDER } from '../utils/constants'

const TUTORS_PER_PAGE = 10
const SEARCH_DEBOUNCE_DELAY = 500 // milliseconds

/**
 * Tutor list page with filtering, sorting, and pagination
 */
function TutorList() {
  const [riskStatus, setRiskStatus] = useState(RISK_STATUS.ALL)
  const [sortBy, setSortBy] = useState(SORT_OPTIONS.NAME)
  const [sortOrder, setSortOrder] = useState(SORT_ORDER.ASC)
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)

  // Debounce search query to avoid too many API calls
  const debouncedSearchQuery = useDebounce(searchQuery, SEARCH_DEBOUNCE_DELAY)

  // Build filters for API (including debounced search)
  const apiFilters = useMemo(() => {
    const filters = {
      limit: TUTORS_PER_PAGE,
      offset: (currentPage - 1) * TUTORS_PER_PAGE,
    }
    if (riskStatus !== RISK_STATUS.ALL) {
      filters.risk_status = riskStatus
    }
    if (sortBy) {
      filters.sort_by = sortBy
    }
    if (sortOrder) {
      filters.sort_order = sortOrder
    }
    // Add debounced search query to API filters (server-side search)
    if (debouncedSearchQuery.trim()) {
      filters.search = debouncedSearchQuery.trim()
    }
    return filters
  }, [riskStatus, sortBy, sortOrder, currentPage, debouncedSearchQuery])

  const { data, isLoading, error, refetch } = useTutors(apiFilters)

  // Reset to page 1 when filters or debounced search change
  useEffect(() => {
    setCurrentPage(1)
  }, [riskStatus, sortBy, sortOrder, debouncedSearchQuery])

  // Use tutors directly from API (server handles filtering, sorting, and search)
  const tutors = data?.tutors || []

  // Calculate pagination info
  const totalTutors = data?.total || 0
  const totalPages = Math.max(1, Math.ceil(totalTutors / TUTORS_PER_PAGE))
  const startIndex = totalTutors > 0 ? (currentPage - 1) * TUTORS_PER_PAGE + 1 : 0
  const endIndex = totalTutors > 0 ? Math.min(currentPage * TUTORS_PER_PAGE, totalTutors) : 0

  // Ensure currentPage is within valid range
  useEffect(() => {
    if (totalPages > 0 && currentPage > totalPages) {
      setCurrentPage(totalPages)
    }
  }, [totalPages, currentPage])

  // Handle page changes
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage)
      // Scroll to top when page changes
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  if (isLoading) {
    return <LoadingSpinner message="Loading tutors..." />
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={refetch} />
  }

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Tutor List</h1>
      </div>

      {/* Filters */}
      <div className="card mb-4 p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Risk Status Filter */}
          <div>
            <label
              htmlFor="risk-status"
              className="block text-xs font-medium text-gray-700 mb-1"
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
              className="block text-xs font-medium text-gray-700 mb-1"
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
              className="block text-xs font-medium text-gray-700 mb-1"
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
        <div className="mt-3">
          <label
            htmlFor="search"
            className="block text-xs font-medium text-gray-700 mb-1"
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
      {tutors.length === 0 && !isLoading ? (
        <div className="card">
          <p className="text-center text-gray-500 py-8">
            {debouncedSearchQuery
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
                  <th className="px-4 py-5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tutor
                  </th>
                  <th className="px-4 py-5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Reschedule Rate (30d)
                  </th>
                  <th className="px-4 py-5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Status
                  </th>
                  <th className="px-4 py-5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Sessions (30d)
                  </th>
                  <th className="px-4 py-5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Updated
                  </th>
                  <th className="px-4 py-5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {tutors.map((tutor) => (
                  <TutorRow key={tutor.id} tutor={tutor} />
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination and Results count */}
          <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                {totalTutors > 0 ? (
                  <>Showing {startIndex} to {endIndex} of {totalTutors} tutors</>
                ) : (
                  <>No tutors found</>
                )}
              </p>

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>

                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TutorList

