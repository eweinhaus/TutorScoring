import { useQuery } from '@tanstack/react-query'
import { getTutors } from '../services/api'

/**
 * Custom hook for fetching tutor list with filtering and polling
 * @param {Object} filters - Filter options (risk_status, sort_by, sort_order, limit, offset)
 * @returns {Object} Query result with data, isLoading, error, refetch
 */
export const useTutors = (filters = {}) => {
  return useQuery({
    queryKey: ['tutors', filters],
    queryFn: () => getTutors(filters),
    staleTime: 30000, // 30 seconds
    refetchInterval: 30000, // Poll every 30 seconds for real-time updates
  })
}

export default useTutors

