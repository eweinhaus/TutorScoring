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
        averageRescheduleRate90d: 0,
        totalSessions30d: 0,
        totalReschedules30d: 0,
        lowRiskCount: 0,
        avgSessionsPerTutor30d: 0,
        highRiskPercentage: 0,
        lowRiskPercentage: 0,
        bestPerformer: null,
        mostActive: null,
      }
    }

    const tutors = data.tutors
    const totalTutors = tutors.length

    // Count high-risk tutors (reschedule_rate_30d >= threshold)
    const highRiskCount = tutors.filter((tutor) => {
      const rate = tutor.reschedule_rate_30d || tutor.tutor_score?.reschedule_rate_30d || 0
      return rate >= RISK_THRESHOLD
    }).length

    // Calculate average reschedule rate (30d)
    const totalRate = tutors.reduce((sum, tutor) => {
      return sum + (tutor.reschedule_rate_30d || tutor.tutor_score?.reschedule_rate_30d || 0)
    }, 0)
    const averageRescheduleRate = totalTutors > 0 ? totalRate / totalTutors : 0

    // Calculate average reschedule rate (90d)
    const totalRate90d = tutors.reduce((sum, tutor) => {
      return sum + (tutor.reschedule_rate_90d || tutor.tutor_score?.reschedule_rate_90d || 0)
    }, 0)
    const averageRescheduleRate90d = totalTutors > 0 ? totalRate90d / totalTutors : 0

    // Calculate total sessions and reschedules (30d)
    const totalSessions30d = tutors.reduce((sum, tutor) => {
      return sum + (tutor.total_sessions_30d || tutor.tutor_score?.total_sessions_30d || 0)
    }, 0)

    const totalReschedules30d = tutors.reduce((sum, tutor) => {
      return sum + (tutor.tutor_reschedules_30d || tutor.tutor_score?.tutor_reschedules_30d || 0)
    }, 0)

    // Calculate low risk count
    const lowRiskCount = totalTutors - highRiskCount

    // Calculate average sessions per tutor (30d)
    const avgSessionsPerTutor30d = totalTutors > 0 ? Math.round(totalSessions30d / totalTutors) : 0

    // Calculate risk percentages
    const highRiskPercentage = totalTutors > 0 ? (highRiskCount / totalTutors) * 100 : 0
    const lowRiskPercentage = totalTutors > 0 ? (lowRiskCount / totalTutors) * 100 : 0

    // Find best and worst performing tutors
    const tutorsWithRates = tutors
      .map(tutor => ({
        tutor,
        rate: tutor.reschedule_rate_30d || tutor.tutor_score?.reschedule_rate_30d || 0,
        sessions: tutor.total_sessions_30d || tutor.tutor_score?.total_sessions_30d || 0
      }))
      .filter(t => t.sessions > 0) // Only tutors with sessions

    const bestPerformer = tutorsWithRates.length > 0
      ? tutorsWithRates.reduce((best, current) => 
          current.rate < best.rate ? current : best
        )
      : null

    const mostActive = tutorsWithRates.length > 0
      ? tutorsWithRates.reduce((most, current) => 
          current.sessions > most.sessions ? current : most
        )
      : null

    return {
      totalTutors,
      highRiskCount,
      averageRescheduleRate,
      averageRescheduleRate90d,
      totalSessions30d,
      totalReschedules30d,
      lowRiskCount,
      avgSessionsPerTutor30d,
      highRiskPercentage,
      lowRiskPercentage,
      bestPerformer,
      mostActive,
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatsCard
          label="Total Tutors"
          value={stats.totalTutors}
          icon="users"
          color="primary"
        />
        <StatsCard
          label="Tutors at Risk"
          value={stats.highRiskCount}
          icon="alert-triangle"
          color={stats.highRiskCount > 0 ? 'danger' : 'success'}
        />
        <StatsCard
          label="Avg Reschedule Rate (30d)"
          value={formatPercentage(stats.averageRescheduleRate)}
          icon="percentage"
          color={
            stats.averageRescheduleRate >= RISK_THRESHOLD
              ? 'danger'
              : stats.averageRescheduleRate >= RISK_THRESHOLD * 0.67
              ? 'warning'
              : 'success'
          }
        />
        <StatsCard
          label="Avg Reschedule Rate (90d)"
          value={formatPercentage(stats.averageRescheduleRate90d)}
          icon="trending-up"
          color={
            stats.averageRescheduleRate90d >= RISK_THRESHOLD
              ? 'danger'
              : stats.averageRescheduleRate90d >= RISK_THRESHOLD * 0.67
              ? 'warning'
              : 'success'
          }
        />
      </div>

      {/* Quick Actions */}
      <div className="card mb-8 py-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Quick Actions</h2>
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
      </div>

      {/* Summary Statistics Section */}
      <div className="card mb-8">
        <h2 className="text-xl font-semibold mb-4">Summary Statistics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">Total Sessions (30d)</p>
            <p className="text-2xl font-bold text-gray-900">
              {stats.totalSessions30d.toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Total Reschedules (30d)</p>
            <p className="text-2xl font-bold text-gray-900">
              {stats.totalReschedules30d.toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Low Risk Tutors</p>
            <p className="text-2xl font-bold text-green-600">
              {stats.lowRiskCount}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Avg Sessions/Tutor (30d)</p>
            <p className="text-2xl font-bold text-gray-900">
              {stats.avgSessionsPerTutor30d}
            </p>
          </div>
        </div>
      </div>

      {/* Risk Overview Section */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Risk Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">High Risk</p>
              <p className="text-lg font-bold text-red-600">{stats.highRiskCount}</p>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-red-600 h-2 rounded-full transition-all"
                style={{ width: `${stats.highRiskPercentage}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">{stats.highRiskPercentage.toFixed(1)}% of tutors</p>
          </div>
          
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">Low Risk</p>
              <p className="text-lg font-bold text-green-600">{stats.lowRiskCount}</p>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full transition-all"
                style={{ width: `${stats.lowRiskPercentage}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">{stats.lowRiskPercentage.toFixed(1)}% of tutors</p>
          </div>

          {stats.bestPerformer && (
            <div>
              <p className="text-sm text-gray-600 mb-1">Best Performer</p>
              <p className="text-sm font-semibold text-gray-900 truncate">
                {stats.bestPerformer.tutor.name}
              </p>
              <p className="text-xs text-gray-500">
                {formatPercentage(stats.bestPerformer.rate)} reschedule rate
              </p>
            </div>
          )}

          {stats.mostActive && (
            <div>
              <p className="text-sm text-gray-600 mb-1">Most Active</p>
              <p className="text-sm font-semibold text-gray-900 truncate">
                {stats.mostActive.tutor.name}
              </p>
              <p className="text-xs text-gray-500">
                {stats.mostActive.sessions} sessions (30d)
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard

