import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { getMatchPrediction, getStudent, getTutor } from '../../services/matchingApi'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import ErrorMessage from '../common/ErrorMessage'
import { formatChurnProbability } from '../../utils/formatters'

function MatchDetailModal({ studentId, tutorId, isOpen, onClose }) {
  // Fetch match prediction
  const {
    data: matchPrediction,
    isLoading: matchLoading,
    error: matchError,
  } = useQuery({
    queryKey: ['match-prediction', studentId, tutorId],
    queryFn: () => getMatchPrediction(studentId, tutorId),
    enabled: isOpen && !!studentId && !!tutorId,
  })

  // Fetch student and tutor names for modal title
  const { data: student } = useQuery({
    queryKey: ['student', studentId],
    queryFn: () => getStudent(studentId),
    enabled: isOpen && !!studentId,
  })

  const { data: tutor } = useQuery({
    queryKey: ['matching-tutor', tutorId],
    queryFn: () => getTutor(tutorId),
    enabled: isOpen && !!tutorId,
  })

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

  const modalTitle = student && tutor 
    ? `Match: ${student.name} & ${tutor.name}`
    : 'Match Details'

  // Convert mismatch scores to match percentages (0-100%)
  const calculateMatchScore = (mismatch, maxMismatch) => {
    if (!mismatch) return 0
    const match = Math.max(0, (maxMismatch - parseFloat(mismatch)) / maxMismatch * 100)
    return Math.min(100, match)
  }

  // Calculate match scores when prediction is available
  const paceMatch = matchPrediction ? calculateMatchScore(matchPrediction.pace_mismatch, 4) : 0
  const styleMatch = matchPrediction ? calculateMatchScore(matchPrediction.style_mismatch, 1) : 0
  const communicationMatch = matchPrediction ? calculateMatchScore(matchPrediction.communication_mismatch, 4) : 0

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={modalTitle} size="md">
      {matchLoading && <LoadingSpinner message="Loading match details..." />}
      {matchError && <ErrorMessage message={matchError.message || 'Failed to load match details'} />}
      
      {matchPrediction && (
        <div className="space-y-4">
          {/* Risk Level & Compatibility */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-gray-600">Churn Risk</span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getRiskColor(matchPrediction.risk_level)}`}>
                  {matchPrediction.risk_level?.toUpperCase()}
                </span>
              </div>
              <div className="text-xs text-gray-500">
                {formatChurnProbability(matchPrediction.churn_probability)} probability
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-gray-600">Compatibility</span>
                <span className="text-lg font-bold text-gray-900">
                  {(parseFloat(matchPrediction.compatibility_score) * 100).toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all"
                  style={{ width: `${(parseFloat(matchPrediction.compatibility_score) * 100).toFixed(0)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Match Scores */}
          <div>
            <h3 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">
              Match Scores
            </h3>
            <div className="grid grid-cols-3 gap-2">
              <div className="bg-gray-50 rounded p-2">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-medium text-gray-700">Pace</span>
                  <span className="text-sm font-semibold text-gray-900">{paceMatch.toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className="bg-green-500 h-1.5 rounded-full"
                    style={{ width: `${paceMatch}%` }}
                  />
                </div>
              </div>
              
              <div className="bg-gray-50 rounded p-2">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-medium text-gray-700">Style</span>
                  <span className="text-sm font-semibold text-gray-900">{styleMatch.toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className="bg-green-500 h-1.5 rounded-full"
                    style={{ width: `${styleMatch}%` }}
                  />
                </div>
              </div>
              
              <div className="bg-gray-50 rounded p-2">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-medium text-gray-700">Communication</span>
                  <span className="text-sm font-semibold text-gray-900">{communicationMatch.toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className="bg-green-500 h-1.5 rounded-full"
                    style={{ width: `${communicationMatch}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Age Difference */}
          <div className="text-center">
            <span className="text-xs text-gray-600">Age Difference: </span>
            <span className="text-xs font-medium text-gray-900">{matchPrediction.age_difference} years</span>
          </div>
        </div>
      )}
    </Modal>
  )
}

export default MatchDetailModal
