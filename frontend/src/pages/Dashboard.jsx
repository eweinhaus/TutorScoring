import React, { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useTutors } from '../hooks/useTutors'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import StatsCard from '../components/charts/StatsCard'
import { RISK_THRESHOLD, RISK_STATUS } from '../utils/constants'
import { formatPercentage } from '../utils/formatters'

/**
 * Dashboard page showing overview statistics
 */
function Dashboard() {
  const { data, isLoading, error, refetch } = useTutors()

  // Calculate summary statistics
  const stats = useMemo(() => {
    if (!data || !data.tutors || data.tutors.length === 0) {
      return {
        totalTutors: 0,
        highRiskCount: 0,
        averageRescheduleRate: 0,
        recentActivity: 0,
      }
    }

    const tutors = data.tutors
    const totalTutors = tutors.length

    // Count high-risk tutors (reschedule_rate_30d >= threshold)
    const highRiskCount = tutors.filter((tutor) => {
      const rate = tutor.reschedule_rate_30d || tutor.tutor_score?.reschedule_rate_30d || 0
      return rate >= RISK_THRESHOLD
    }).length

    // Calculate average reschedule rate
    const totalRate = tutors.reduce((sum, tutor) => {
      return sum + (tutor.reschedule_rate_30d || tutor.tutor_score?.reschedule_rate_30d || 0)
    }, 0)
    const averageRescheduleRate = totalTutors > 0 ? totalRate / totalTutors : 0

    // Count recent activity (tutors with sessions in last 7 days)
    // For now, we'll use tutors with recent score calculations as a proxy
    const recentActivity = tutors.filter((tutor) => {
      const lastUpdated = tutor.last_calculated_at || tutor.tutor_score?.last_calculated_at || tutor.updated_at
      if (!lastUpdated) return false
      const daysSinceUpdate =
        (Date.now() - new Date(lastUpdated).getTime()) / (1000 * 60 * 60 * 24)
      return daysSinceUpdate <= 7
    }).length

    return {
      totalTutors,
      highRiskCount,
      averageRescheduleRate,
      recentActivity,
    }
  }, [data])

  if (isLoading) {
    return <LoadingSpinner message="Loading dashboard..." />
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={refetch} />
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-600">
          Overview of tutor performance and quality metrics
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          label="Total Tutors"
          value={stats.totalTutors}
          color="primary"
        />
        <StatsCard
          label="High-Risk Tutors"
          value={stats.highRiskCount}
          color={stats.highRiskCount > 0 ? 'danger' : 'success'}
        />
        <StatsCard
          label="Average Reschedule Rate"
          value={formatPercentage(stats.averageRescheduleRate)}
          color={
            stats.averageRescheduleRate >= RISK_THRESHOLD
              ? 'danger'
              : stats.averageRescheduleRate >= RISK_THRESHOLD * 0.67
              ? 'warning'
              : 'success'
          }
        />
        <StatsCard
          label="Recent Activity"
          value={stats.recentActivity}
          color="primary"
        />
      </div>

      {/* Quick Actions */}
      <div className="card mb-8">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-4">
          <Link
            to="/tutors"
            className="btn btn-primary"
          >
            View All Tutors
          </Link>
          <Link
            to={`/tutors?risk_status=${RISK_STATUS.HIGH}`}
            className="btn btn-secondary"
          >
            View High-Risk Tutors
          </Link>
        </div>
      </div>

      {/* Recent Activity Section */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">System Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">Total Tutors Monitored</p>
            <p className="text-2xl font-bold text-gray-900">{stats.totalTutors}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">High-Risk Threshold</p>
            <p className="text-2xl font-bold text-gray-900">
              {RISK_THRESHOLD}%
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

