import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { getMatchPrediction } from '../../services/matchingApi'
import LoadingSpinner from '../common/LoadingSpinner'
import ErrorMessage from '../common/ErrorMessage'
import RiskBadge from '../common/RiskBadge'

function MatchDetailPanel({ studentId, tutorId, matchPrediction, isLoading, error }) {
  const getRiskColor = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'low':
        return 'bg-green-100 text-green-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'high':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <LoadingSpinner message="Loading match details..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <ErrorMessage message={error.message || 'Failed to load match details'} />
      </div>
    )
  }

  if (!matchPrediction) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <p className="text-gray-500">No match prediction available</p>
      </div>
    )
  }

  const compatibilityPercent = (parseFloat(matchPrediction.compatibility_score) * 100).toFixed(0)
  const churnPercent = (parseFloat(matchPrediction.churn_probability) * 100).toFixed(1)

  return (
    <div className="bg-white rounded-lg shadow p-4 space-y-4">
      <h2 className="text-xl font-semibold">Match Details</h2>

      {/* Risk Level */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Churn Risk</span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(matchPrediction.risk_level)}`}>
            {matchPrediction.risk_level?.toUpperCase()}
          </span>
        </div>
        <div className="text-sm text-gray-600">
          {churnPercent}% probability of churn
        </div>
      </div>

      {/* Compatibility Score */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Compatibility</span>
          <span className="text-lg font-bold">{compatibilityPercent}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-primary h-2 rounded-full transition-all"
            style={{ width: `${compatibilityPercent}%` }}
          />
        </div>
      </div>

      {/* Mismatch Scores */}
      <div>
        <h3 className="text-sm font-medium mb-2">Mismatch Analysis</h3>
        <div className="space-y-2">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Pace</span>
              <span>{parseFloat(matchPrediction.pace_mismatch).toFixed(1)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div
                className="bg-yellow-500 h-1.5 rounded-full"
                style={{ width: `${Math.min(parseFloat(matchPrediction.pace_mismatch) * 25, 100)}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Style</span>
              <span>{parseFloat(matchPrediction.style_mismatch).toFixed(1)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div
                className="bg-yellow-500 h-1.5 rounded-full"
                style={{ width: `${parseFloat(matchPrediction.style_mismatch) * 100}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Communication</span>
              <span>{parseFloat(matchPrediction.communication_mismatch).toFixed(1)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div
                className="bg-yellow-500 h-1.5 rounded-full"
                style={{ width: `${Math.min(parseFloat(matchPrediction.communication_mismatch) * 25, 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* AI Explanation */}
      {matchPrediction.ai_explanation && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <h3 className="text-sm font-medium mb-2 text-blue-900">AI Analysis</h3>
          <p className="text-sm text-blue-800">{matchPrediction.ai_explanation}</p>
        </div>
      )}
    </div>
  )
}

export default MatchDetailPanel

