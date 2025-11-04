import { useQuery } from '@tanstack/react-query'
import { getTutor, getTutorHistory } from '../services/api'

/**
 * Custom hook for fetching tutor detail and history
 * @param {string} tutorId - Tutor ID
 * @returns {Object} Combined query result with tutor, history, isLoading, error
 */
export const useTutorDetail = (tutorId) => {
  const tutorQuery = useQuery({
    queryKey: ['tutor', tutorId],
    queryFn: () => getTutor(tutorId),
    enabled: !!tutorId, // Only run if tutorId exists
    staleTime: 30000,
    refetchInterval: 30000,
  })

  const historyQuery = useQuery({
    queryKey: ['tutor-history', tutorId],
    queryFn: () => getTutorHistory(tutorId),
    enabled: !!tutorId, // Only run if tutorId exists
    staleTime: 30000,
    refetchInterval: 30000,
  })

  return {
    tutor: tutorQuery.data,
    history: historyQuery.data,
    isLoading: tutorQuery.isLoading || historyQuery.isLoading,
    error: tutorQuery.error || historyQuery.error,
    refetch: () => {
      tutorQuery.refetch()
      historyQuery.refetch()
    },
  }
}

export default useTutorDetail

