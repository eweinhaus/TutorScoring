import React, { useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTutorDetail } from '../hooks/useTutorDetail'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import RiskBadge from '../components/common/RiskBadge'
import RescheduleTable from '../components/tutor/RescheduleTable'
import { formatPercentage, formatDate } from '../utils/formatters'

/**
 * Tutor detail page showing comprehensive tutor performance metrics
 */
function TutorDetail() {
  const { id } = useParams()
  const { tutor, history, isLoading, error, refetch } = useTutorDetail(id)

  // Normalize tutor score data - handle both API response formats
  const tutorScore = useMemo(() => {
    if (!tutor) return null
    return tutor.scores || tutor.statistics || tutor.tutor_score || null
  }, [tutor])

  // Get recent reschedules (last 10-20)
  const recentReschedules = useMemo(() => {
    if (!history || !history.reschedules) return []
    return history.reschedules.slice(0, 20)
  }, [history])


  if (isLoading) {
    return <LoadingSpinner message="Loading tutor details..." />
  }

  if (error) {
    // Check if it's a 404 error
    const isNotFound = error.message && (error.message.includes('not found') || error.message.includes('404'))
    
    return (
      <div className="card p-4">
        <h2 className="text-lg font-semibold mb-3">Tutor Not Found</h2>
        <p className="text-sm text-gray-600 mb-3">
          {isNotFound 
            ? "The tutor you're looking for doesn't exist or has been removed. This may be due to data regeneration."
            : "Unable to load tutor information. Please try again."}
        </p>
        <div className="flex gap-3">
          <Link to="/tutors" className="btn btn-primary">
            Back to Tutor List
          </Link>
          {!isNotFound && (
            <button onClick={refetch} className="btn btn-secondary">
              Retry
            </button>
          )}
        </div>
      </div>
    )
  }

  if (!tutor) {
    return (
      <div className="card p-4">
        <h2 className="text-lg font-semibold mb-3">Tutor Not Found</h2>
        <p className="text-sm text-gray-600 mb-3">
          The tutor you're looking for doesn't exist or has been removed.
        </p>
        <Link to="/tutors" className="btn btn-primary">
          Back to Tutor List
        </Link>
      </div>
    )
  }

  // Use normalized tutorScore (already calculated above)
  // Ensure score is an object with safe defaults
  const score = tutorScore || {}
  
  // Safely extract rate for RiskBadge - handle string values and NaN
  let rescheduleRate30d = null
  if (score.reschedule_rate_30d != null) {
    const parsed = typeof score.reschedule_rate_30d === 'string' 
      ? parseFloat(score.reschedule_rate_30d) 
      : Number(score.reschedule_rate_30d)
    if (!isNaN(parsed) && isFinite(parsed)) {
      rescheduleRate30d = parsed
    }
  }

  return (
    <div>
      {/* Back Navigation */}
      <div className="mb-3">
        <Link
          to="/tutors"
          className="text-primary hover:text-primary-dark flex items-center text-sm"
        >
          <svg
            className="w-4 h-4 mr-1"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Back to Tutor List
        </Link>
      </div>

      {/* Tutor Header */}
      <div className="card mb-4 p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">
              {tutor.name}
            </h1>
            <p className="text-sm text-gray-600">{tutor.email || 'No email provided'}</p>
          </div>
          {rescheduleRate30d !== null && (
          <RiskBadge rate={rescheduleRate30d} size="large" />
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-200">
          <div>
            <p className="text-xs text-gray-600 mb-1">Total Sessions (90d)</p>
            <p className="text-xl font-bold text-gray-900">
              {score.total_sessions_90d || 0}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Reschedule Rate (90d)</p>
            <p className="text-xl font-bold text-gray-900">
              {formatPercentage(score.reschedule_rate_90d)}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Last Updated</p>
            <p className="text-xl font-bold text-gray-900">
              {formatDate(score.last_calculated_at || tutor.updated_at)}
            </p>
          </div>
        </div>
      </div>

      {/* Recent Reschedules Table */}
      <div className="mb-4">
        <h2 className="text-lg font-semibold mb-3">Recent Reschedules</h2>
        <RescheduleTable reschedules={recentReschedules} sortable={true} />
      </div>
    </div>
  )
}

export default TutorDetail

