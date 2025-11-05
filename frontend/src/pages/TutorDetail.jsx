import React, { useState, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTutorDetail } from '../hooks/useTutorDetail'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import RiskBadge from '../components/common/RiskBadge'
import RescheduleTable from '../components/tutor/RescheduleTable'
import RescheduleRateChart from '../components/charts/RescheduleRateChart'
import StatsCard from '../components/charts/StatsCard'
import { RISK_THRESHOLD, TIME_PERIODS } from '../utils/constants'
import { formatPercentage, formatDate } from '../utils/formatters'

/**
 * Tutor detail page showing comprehensive tutor performance metrics
 */
function TutorDetail() {
  const { id } = useParams()
  const { tutor, history, isLoading, error, refetch } = useTutorDetail(id)
  const [selectedTimePeriod, setSelectedTimePeriod] = useState('30d')

  // Normalize tutor score data - handle both API response formats
  const tutorScore = useMemo(() => {
    if (!tutor) return null
    return tutor.scores || tutor.statistics || tutor.tutor_score || null
  }, [tutor])

  // Prepare chart data from history
  const chartData = useMemo(() => {
    if (!history || !history.reschedules || history.reschedules.length === 0) {
      return []
    }

    // Group reschedules by date and calculate rates
    // For MVP, we'll use the tutor_score data if available
    // Otherwise, create simplified data points
    if (tutorScore) {
      // Create data points from tutor score history (if available)
      // For now, we'll show current rates as a single data point
      return [
        {
          date: tutorScore.last_calculated_at || new Date().toISOString(),
          rate7d: tutorScore.reschedule_rate_7d || 0,
          rate30d: tutorScore.reschedule_rate_30d || 0,
          rate90d: tutorScore.reschedule_rate_90d || 0,
        },
      ]
    }

    return []
  }, [history, tutorScore])

  // Get recent reschedules (last 10-20)
  const recentReschedules = useMemo(() => {
    if (!history || !history.reschedules) return []
    return history.reschedules.slice(0, 20)
  }, [history])

  // Generate insights
  const insights = useMemo(() => {
    if (!tutorScore) {
      return {
        riskLevel: 'Unknown',
        description: 'No data available',
        recommendations: [],
      }
    }

    const score = tutorScore
    // Convert string values to numbers for proper comparison
    const rate30d = score.reschedule_rate_30d != null ? parseFloat(score.reschedule_rate_30d) || 0 : 0
    const rate7d = score.reschedule_rate_7d != null ? parseFloat(score.reschedule_rate_7d) || 0 : 0
    const totalReschedules = score.tutor_reschedules_30d || 0
    const totalSessions = score.total_sessions_30d || 0

    let riskLevel = 'Low Risk'
    let description = 'This tutor is performing well.'
    const recommendations = []

    if (rate30d >= RISK_THRESHOLD) {
      riskLevel = 'High Risk'
      description = `This tutor has a reschedule rate of ${formatPercentage(
        rate30d
      )}, which exceeds the ${RISK_THRESHOLD}% threshold.`
      recommendations.push(
        'Review recent reschedule patterns and reasons',
        'Consider scheduling a performance review',
        'Monitor closely for the next 7 days'
      )
    } else if (rate30d >= RISK_THRESHOLD * 0.67) {
      riskLevel = 'Warning'
      description = `This tutor is approaching the high-risk threshold with a ${formatPercentage(
        rate30d
      )} reschedule rate.`
      recommendations.push(
        'Monitor reschedule patterns',
        'Consider proactive outreach'
      )
    }

    if (rate7d > rate30d) {
      recommendations.push(
        'Recent reschedule rate is higher than 30-day average - investigate recent issues'
      )
    }

    if (totalReschedules > 0 && totalSessions > 0) {
      recommendations.push(
        `${totalReschedules} reschedule${totalReschedules !== 1 ? 's' : ''} in the past 30 days out of ${totalSessions} total session${totalSessions !== 1 ? 's' : ''}`
      )
    }

    return {
      riskLevel,
      description,
      recommendations,
    }
  }, [tutorScore])

  if (isLoading) {
    return <LoadingSpinner message="Loading tutor details..." />
  }

  if (error) {
    // Check if it's a 404 error
    const isNotFound = error.message && (error.message.includes('not found') || error.message.includes('404'))
    
    return (
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Tutor Not Found</h2>
        <p className="text-gray-600 mb-4">
          {isNotFound 
            ? "The tutor you're looking for doesn't exist or has been removed. This may be due to data regeneration."
            : "Unable to load tutor information. Please try again."}
        </p>
        <div className="flex gap-4">
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
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Tutor Not Found</h2>
        <p className="text-gray-600 mb-4">
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
      <div className="mb-4">
        <Link
          to="/tutors"
          className="text-primary hover:text-primary-dark flex items-center"
        >
          <svg
            className="w-5 h-5 mr-2"
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
      <div className="card mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {tutor.name}
            </h1>
            <p className="text-gray-600 mb-4">{tutor.email || 'No email provided'}</p>
          </div>
          {rescheduleRate30d !== null && (
          <RiskBadge rate={rescheduleRate30d} size="large" />
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-200">
          <div>
            <p className="text-sm text-gray-600 mb-1">Total Sessions (30d)</p>
            <p className="text-2xl font-bold text-gray-900">
              {score.total_sessions_30d || 0}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Reschedule Rate (30d)</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatPercentage(score.reschedule_rate_30d)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Last Updated</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatDate(score.last_calculated_at || tutor.updated_at)}
            </p>
          </div>
        </div>
      </div>

      {/* Reschedule Rate Chart */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Reschedule Rate Trends</h2>
          <div className="flex gap-2">
            {TIME_PERIODS.map((period) => (
              <button
                key={period}
                onClick={() => setSelectedTimePeriod(period)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedTimePeriod === period
                    ? 'bg-primary text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {period.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
        <RescheduleRateChart
          data={chartData}
          threshold={RISK_THRESHOLD}
          timePeriod={selectedTimePeriod}
        />
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <StatsCard
          label="Total Sessions (7d)"
          value={score.total_sessions_7d || 0}
          color="primary"
        />
        <StatsCard
          label="Total Sessions (30d)"
          value={score.total_sessions_30d || 0}
          color="primary"
        />
        <StatsCard
          label="Total Sessions (90d)"
          value={score.total_sessions_90d || 0}
          color="primary"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <StatsCard
          label="Reschedules (7d)"
          value={score.tutor_reschedules_7d || 0}
          color="warning"
        />
        <StatsCard
          label="Reschedules (30d)"
          value={score.tutor_reschedules_30d || 0}
          color="warning"
        />
        <StatsCard
          label="Reschedules (90d)"
          value={score.tutor_reschedules_90d || 0}
          color="warning"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <StatsCard
          label="Rate (7d)"
          value={formatPercentage(score.reschedule_rate_7d)}
          color={
            (score.reschedule_rate_7d || 0) >= RISK_THRESHOLD
              ? 'danger'
              : (score.reschedule_rate_7d || 0) >= RISK_THRESHOLD * 0.67
              ? 'warning'
              : 'success'
          }
        />
        <StatsCard
          label="Rate (30d)"
          value={formatPercentage(score.reschedule_rate_30d)}
          color={
            (score.reschedule_rate_30d || 0) >= RISK_THRESHOLD
              ? 'danger'
              : (score.reschedule_rate_30d || 0) >= RISK_THRESHOLD * 0.67
              ? 'warning'
              : 'success'
          }
        />
        <StatsCard
          label="Rate (90d)"
          value={formatPercentage(score.reschedule_rate_90d)}
          color={
            (score.reschedule_rate_90d || 0) >= RISK_THRESHOLD
              ? 'danger'
              : (score.reschedule_rate_90d || 0) >= RISK_THRESHOLD * 0.67
              ? 'warning'
              : 'success'
          }
        />
      </div>

      {/* Recent Reschedules Table */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Recent Reschedules</h2>
        <RescheduleTable reschedules={recentReschedules} sortable={true} />
      </div>

      {/* Insights & Recommendations */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Insights & Recommendations</h2>
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Risk Level: {insights.riskLevel}
            </h3>
            <p className="text-gray-600">{insights.description}</p>
          </div>

          {insights.recommendations.length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Recommendations
              </h3>
              <ul className="list-disc list-inside space-y-2 text-gray-600">
                {insights.recommendations.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default TutorDetail

