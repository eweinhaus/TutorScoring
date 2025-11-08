import { useQuery } from '@tanstack/react-query'
import { getUpcomingSessions } from '../services/upcomingSessionsApi'

/**
 * React Query hook for fetching upcoming sessions with reschedule predictions.
 * 
 * @param {Object} params - Query parameters
 * @param {number} params.days_ahead - Number of days ahead to show (default: 7)
 * @param {string} params.risk_level - Filter by risk level (low/medium/high)
 * @param {string} params.tutor_id - Filter by tutor ID
 * @param {number} params.limit - Pagination limit (default: 50)
 * @param {number} params.offset - Pagination offset (default: 0)
 * @param {string} params.sort_by - Sort field
 * @param {string} params.sort_order - Sort order (asc/desc)
 * @returns {Object} Query result with sessions, total, isLoading, error, refetch
 */
export function useUpcomingSessions(params = {}) {
  const {
    days_ahead = 7,
    risk_level,
    tutor_id,
    limit = 50,
    offset = 0,
    sort_by = 'scheduled_time',
    sort_order = 'asc',
  } = params

  const queryParams = {
    days_ahead,
    ...(risk_level && { risk_level }),
    ...(tutor_id && { tutor_id }),
    limit,
    offset,
    sort_by,
    sort_order,
  }

  const query = useQuery({
    queryKey: ['upcoming-sessions', queryParams],
    queryFn: () => getUpcomingSessions(queryParams),
    staleTime: 10 * 1000, // 10 seconds
    refetchInterval: 30 * 1000, // Poll every 30 seconds (same as existing dashboard)
  })

  return {
    sessions: query.data?.sessions || [],
    total: query.data?.total || 0,
    limit: query.data?.limit || limit,
    offset: query.data?.offset || offset,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  }
}


