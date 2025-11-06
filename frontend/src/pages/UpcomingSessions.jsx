import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'
import UpcomingSessionsTable from '../components/sessions/UpcomingSessionsTable'
import { UPCOMING_SESSIONS_SORT_OPTIONS, SORT_ORDER } from '../utils/constants'

/**
 * Upcoming Sessions page showing sessions with reschedule predictions
 */
function UpcomingSessions() {
  const [daysAhead, setDaysAhead] = useState(7)
  const [riskLevel, setRiskLevel] = useState('all')
  const [sortBy, setSortBy] = useState(UPCOMING_SESSIONS_SORT_OPTIONS.SCHEDULED_TIME)
  const [sortOrder, setSortOrder] = useState(SORT_ORDER.ASC)
  
  // Fetch upcoming sessions
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['upcomingSessions', daysAhead, riskLevel, sortBy, sortOrder],
    queryFn: async () => {
      const params = new URLSearchParams({
        days_ahead: daysAhead,
        sort_by: sortBy,
        sort_order: sortOrder,
        limit: 500, // Get all sessions for now
      })
      
      if (riskLevel !== 'all') {
        params.append('risk_level', riskLevel)
      }
      
      const API_KEY = import.meta.env.VITE_API_KEY
      const headers = API_KEY ? { 'X-API-Key': API_KEY } : {}
      
      const response = await axios.get(`/api/upcoming-sessions?${params.toString()}`, {
        headers
      })
      return response.data
    },
    refetchInterval: 60000, // Refetch every minute
  })
  
  const handleSort = (field, order) => {
    setSortBy(field)
    setSortOrder(order)
  }
  
  const sessions = data?.sessions || []
  const total = data?.total || 0
  
  // Calculate stats
  const highRiskCount = sessions.filter(s => s.risk_level === 'high').length
  const mediumRiskCount = sessions.filter(s => s.risk_level === 'medium').length
  const lowRiskCount = sessions.filter(s => s.risk_level === 'low').length
  
  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upcoming Sessions</h1>
        <p className="text-gray-600">
          View upcoming sessions with AI-powered reschedule predictions
        </p>
      </div>
      
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <div className="text-sm font-medium text-gray-500 mb-1">Total Sessions</div>
          <div className="text-3xl font-bold text-gray-900">{total}</div>
        </div>
        <div className="card">
          <div className="text-sm font-medium text-gray-500 mb-1">High Risk</div>
          <div className="text-3xl font-bold text-red-600">{highRiskCount}</div>
        </div>
        <div className="card">
          <div className="text-sm font-medium text-gray-500 mb-1">Medium Risk</div>
          <div className="text-3xl font-bold text-yellow-600">{mediumRiskCount}</div>
        </div>
        <div className="card">
          <div className="text-sm font-medium text-gray-500 mb-1">Low Risk</div>
          <div className="text-3xl font-bold text-green-600">{lowRiskCount}</div>
        </div>
      </div>
      
      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Days Ahead Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Time Range
            </label>
            <select
              value={daysAhead}
              onChange={(e) => setDaysAhead(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value={1}>Next 1 day</option>
              <option value={3}>Next 3 days</option>
              <option value={7}>Next 7 days</option>
              <option value={14}>Next 14 days</option>
              <option value={30}>Next 30 days</option>
            </select>
          </div>
          
          {/* Risk Level Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Risk Level
            </label>
            <select
              value={riskLevel}
              onChange={(e) => setRiskLevel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">All Risk Levels</option>
              <option value="high">High Risk Only</option>
              <option value="medium">Medium Risk Only</option>
              <option value="low">Low Risk Only</option>
            </select>
          </div>
        </div>
      </div>
      
      {/* Sessions Table */}
      <div className="card">
        {isLoading ? (
          <LoadingSpinner message="Loading upcoming sessions..." />
        ) : error ? (
          <ErrorMessage error={error} onRetry={refetch} />
        ) : (
          <>
            <div className="mb-4">
              <h2 className="text-xl font-semibold text-gray-900">
                Sessions ({sessions.length})
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Sorted by {sortBy.replace(/_/g, ' ')} ({sortOrder})
              </p>
            </div>
            <UpcomingSessionsTable
              sessions={sessions}
              onSort={handleSort}
              sortBy={sortBy}
              sortOrder={sortOrder}
            />
          </>
        )}
      </div>
    </div>
  )
}

export default UpcomingSessions
