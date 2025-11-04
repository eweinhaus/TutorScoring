import React, { memo } from 'react'
import { useNavigate } from 'react-router-dom'
import RiskBadge from '../common/RiskBadge'
import { formatPercentage, formatDate } from '../../utils/formatters'

/**
 * Tutor card component for displaying tutor summary
 * @param {Object} tutor - Tutor data object
 * @param {Function} onClick - Optional click handler
 */
function TutorCard({ tutor, onClick }) {
  const navigate = useNavigate()

  const handleClick = () => {
    if (onClick) {
      onClick()
    } else {
      navigate(`/tutors/${tutor.id}`)
    }
  }

  const rescheduleRate = tutor.tutor_score?.reschedule_rate_30d || 0
  const totalSessions = tutor.tutor_score?.total_sessions_30d || 0
  const lastUpdated = tutor.tutor_score?.last_calculated_at || tutor.updated_at

  return (
    <div
      className="card hover:shadow-lg transition-shadow cursor-pointer"
      onClick={handleClick}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            {tutor.name}
          </h3>
          <p className="text-sm text-gray-600">{tutor.email}</p>
        </div>
        <RiskBadge rate={rescheduleRate} />
      </div>

      <div className="grid grid-cols-2 gap-4 mt-4">
        <div>
          <p className="text-xs text-gray-500 mb-1">Reschedule Rate</p>
          <p className="text-lg font-semibold text-gray-900">
            {formatPercentage(rescheduleRate)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">Total Sessions (30d)</p>
          <p className="text-lg font-semibold text-gray-900">{totalSessions}</p>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Last updated: {formatDate(lastUpdated)}
        </p>
      </div>
    </div>
  )
}

export default memo(TutorCard)

