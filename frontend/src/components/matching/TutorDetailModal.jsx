import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { getTutor } from '../../services/matchingApi'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import ErrorMessage from '../common/ErrorMessage'

/**
 * Modal component displaying detailed tutor profile information.
 */
function TutorDetailModal({ tutorId, isOpen, onClose }) {
  const {
    data: tutor,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['matching-tutor', tutorId],
    queryFn: () => getTutor(tutorId),
    enabled: isOpen && !!tutorId,
  })

  const formatScale = (value, max) => {
    if (value === null || value === undefined) return 'N/A'
    return `${value}/${max}`
  }

  const getPaceLabel = (pace) => {
    if (!pace) return 'N/A'
    const labels = { 1: 'Very Slow', 2: 'Slow', 3: 'Moderate', 4: 'Fast', 5: 'Very Fast' }
    return labels[pace] || `Pace ${pace}`
  }

  const getCommunicationLabel = (style) => {
    if (!style) return 'N/A'
    const labels = { 1: 'Very Formal', 2: 'Formal', 3: 'Balanced', 4: 'Casual', 5: 'Very Casual' }
    return labels[style] || `Style ${style}`
  }

  const getConfidenceLabel = (confidence) => {
    if (!confidence) return 'N/A'
    const labels = { 1: 'Low', 2: 'Low-Moderate', 3: 'Moderate', 4: 'High-Moderate', 5: 'High' }
    return labels[confidence] || `Confidence ${confidence}`
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Tutor Profile" size="lg">
      {isLoading && <LoadingSpinner message="Loading tutor details..." />}
      {error && <ErrorMessage message={error.message || 'Failed to load tutor details'} />}
      
      {tutor && (
        <div className="space-y-6">
          {/* Basic Information */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
              Basic Information
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-500">Name</span>
                <p className="text-base font-medium text-gray-900">{tutor.name}</p>
              </div>
              {tutor.email && (
                <div>
                  <span className="text-sm text-gray-500">Email</span>
                  <p className="text-base font-medium text-gray-900">{tutor.email}</p>
                </div>
              )}
              {tutor.age && (
                <div>
                  <span className="text-sm text-gray-500">Age</span>
                  <p className="text-base font-medium text-gray-900">{tutor.age} years</p>
                </div>
              )}
              {tutor.sex && (
                <div>
                  <span className="text-sm text-gray-500">Sex</span>
                  <p className="text-base font-medium text-gray-900 capitalize">{tutor.sex}</p>
                </div>
              )}
              {tutor.experience_years !== null && tutor.experience_years !== undefined && (
                <div>
                  <span className="text-sm text-gray-500">Experience</span>
                  <p className="text-base font-medium text-gray-900">
                    {tutor.experience_years} {tutor.experience_years === 1 ? 'year' : 'years'}
                  </p>
                </div>
              )}
              <div>
                <span className="text-sm text-gray-500">Status</span>
                <p className="text-base font-medium">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    tutor.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {tutor.is_active ? 'Active' : 'Inactive'}
                  </span>
                </p>
              </div>
            </div>
          </div>

          {/* Teaching Preferences */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
              Teaching Preferences
            </h3>
            <div className="space-y-3">
              {tutor.teaching_style && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-sm font-medium text-gray-700">Teaching Style</span>
                    <span className="text-sm text-gray-600 capitalize">{tutor.teaching_style}</span>
                  </div>
                </div>
              )}

              {tutor.preferred_pace !== null && tutor.preferred_pace !== undefined && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-sm font-medium text-gray-700">Preferred Pace</span>
                    <span className="text-sm text-gray-600">{formatScale(tutor.preferred_pace, 5)}</span>
                  </div>
                  <p className="text-xs text-gray-500">{getPaceLabel(tutor.preferred_pace)}</p>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${(tutor.preferred_pace / 5) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {tutor.communication_style !== null && tutor.communication_style !== undefined && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-sm font-medium text-gray-700">Communication Style</span>
                    <span className="text-sm text-gray-600">{formatScale(tutor.communication_style, 5)}</span>
                  </div>
                  <p className="text-xs text-gray-500">{getCommunicationLabel(tutor.communication_style)}</p>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${(tutor.communication_style / 5) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {tutor.confidence_level !== null && tutor.confidence_level !== undefined && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-sm font-medium text-gray-700">Confidence Level</span>
                    <span className="text-sm text-gray-600">{formatScale(tutor.confidence_level, 5)}</span>
                  </div>
                  <p className="text-xs text-gray-500">{getConfidenceLabel(tutor.confidence_level)}</p>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-purple-500 h-2 rounded-full"
                      style={{ width: `${(tutor.confidence_level / 5) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {tutor.preferred_student_level && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-sm font-medium text-gray-700">Preferred Student Level</span>
                    <span className="text-sm text-gray-600 capitalize">{tutor.preferred_student_level}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Performance Metrics (if available) */}
          {tutor.tutor_score && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
                Performance Metrics
              </h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <span className="text-xs text-gray-500">7-Day Reschedule Rate</span>
                  <p className="text-lg font-semibold text-gray-900">
                    {tutor.tutor_score.reschedule_rate_7d 
                      ? `${parseFloat(tutor.tutor_score.reschedule_rate_7d).toFixed(1)}%`
                      : 'N/A'}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <span className="text-xs text-gray-500">30-Day Reschedule Rate</span>
                  <p className="text-lg font-semibold text-gray-900">
                    {tutor.tutor_score.reschedule_rate_30d 
                      ? `${parseFloat(tutor.tutor_score.reschedule_rate_30d).toFixed(1)}%`
                      : 'N/A'}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <span className="text-xs text-gray-500">Risk Status</span>
                  <p className="text-lg font-semibold">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      tutor.tutor_score.is_high_risk 
                        ? 'bg-red-100 text-red-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {tutor.tutor_score.is_high_risk ? 'High Risk' : 'Low Risk'}
                    </span>
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Additional Preferences */}
          {tutor.preferences_json && Object.keys(tutor.preferences_json).length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
                Additional Preferences
              </h3>
              <div className="bg-gray-50 rounded-lg p-3">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                  {JSON.stringify(tutor.preferences_json, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  )
}

export default TutorDetailModal

