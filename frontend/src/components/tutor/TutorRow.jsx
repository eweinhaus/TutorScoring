import React, { memo } from 'react'
import { useNavigate } from 'react-router-dom'
import RiskBadge from '../common/RiskBadge'
import { formatPercentage, formatDate, getRiskColor } from '../../utils/formatters'
import { RISK_THRESHOLD } from '../../utils/constants'

/**
 * Tutor row component for table display
 * @param {Object} tutor - Tutor data object
 * @param {Function} onClick - Optional click handler
 */
function TutorRow({ tutor, onClick }) {
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
  const rateColor = getRiskColor(rescheduleRate, RISK_THRESHOLD)

  const colorClasses = {
    red: 'text-red-600 font-semibold',
    yellow: 'text-yellow-600 font-semibold',
    green: 'text-green-600',
  }

  return (
    <tr
      className="border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
      onClick={handleClick}
    >
      <td className="px-6 py-4 whitespace-nowrap">
        <div>
          <div className="text-sm font-medium text-gray-900">{tutor.name}</div>
          <div className="text-sm text-gray-500">{tutor.email}</div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={colorClasses[rateColor]}>
          {formatPercentage(rescheduleRate)}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <RiskBadge rate={rescheduleRate} size="small" />
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        {totalSessions}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {formatDate(lastUpdated)}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <button
          className="text-primary hover:text-primary-dark"
          onClick={(e) => {
            e.stopPropagation()
            handleClick()
          }}
        >
          View Details
        </button>
      </td>
    </tr>
  )
}

export default memo(TutorRow)

