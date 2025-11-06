import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { getStudent } from '../../services/matchingApi'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import ErrorMessage from '../common/ErrorMessage'

/**
 * Modal component displaying detailed student profile information.
 */
function StudentDetailModal({ studentId, isOpen, onClose }) {
  const {
    data: student,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['student', studentId],
    queryFn: () => getStudent(studentId),
    enabled: isOpen && !!studentId,
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

  const getUrgencyLabel = (urgency) => {
    if (!urgency) return 'N/A'
    const labels = { 1: 'Low', 2: 'Low-Moderate', 3: 'Moderate', 4: 'High-Moderate', 5: 'High' }
    return labels[urgency] || `Urgency ${urgency}`
  }

  const getCommunicationLabel = (style) => {
    if (!style) return 'N/A'
    const labels = { 1: 'Very Formal', 2: 'Formal', 3: 'Balanced', 4: 'Casual', 5: 'Very Casual' }
    return labels[style] || `Style ${style}`
  }

  const getSatisfactionLabel = (satisfaction) => {
    if (!satisfaction) return 'N/A'
    const labels = { 1: 'Very Dissatisfied', 2: 'Dissatisfied', 3: 'Neutral', 4: 'Satisfied', 5: 'Very Satisfied' }
    return labels[satisfaction] || `Satisfaction ${satisfaction}`
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Student Profile" size="lg">
      {isLoading && <LoadingSpinner message="Loading student details..." />}
      {error && <ErrorMessage message={error.message || 'Failed to load student details'} />}
      
      {student && (
        <div className="space-y-6">
          {/* Basic Information */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
              Basic Information
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-500">Name</span>
                <p className="text-base font-medium text-gray-900">{student.name}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Age</span>
                <p className="text-base font-medium text-gray-900">{student.age} years</p>
              </div>
              {student.sex && (
                <div>
                  <span className="text-sm text-gray-500">Sex</span>
                  <p className="text-base font-medium text-gray-900 capitalize">{student.sex}</p>
                </div>
              )}
            </div>
          </div>

          {/* Learning Preferences */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
              Learning Preferences
            </h3>
            <div className="space-y-3">
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-sm font-medium text-gray-700">Preferred Pace</span>
                  <span className="text-sm text-gray-600">{formatScale(student.preferred_pace, 5)}</span>
                </div>
                <p className="text-xs text-gray-500">{getPaceLabel(student.preferred_pace)}</p>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${(student.preferred_pace / 5) * 100}%` }}
                  />
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-3">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-sm font-medium text-gray-700">Teaching Style</span>
                  <span className="text-sm text-gray-600 capitalize">{student.preferred_teaching_style || 'N/A'}</span>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-3">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-sm font-medium text-gray-700">Communication Style</span>
                  <span className="text-sm text-gray-600">{formatScale(student.communication_style_preference, 5)}</span>
                </div>
                <p className="text-xs text-gray-500">{getCommunicationLabel(student.communication_style_preference)}</p>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${(student.communication_style_preference / 5) * 100}%` }}
                  />
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-3">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-sm font-medium text-gray-700">Urgency Level</span>
                  <span className="text-sm text-gray-600">{formatScale(student.urgency_level, 5)}</span>
                </div>
                <p className="text-xs text-gray-500">{getUrgencyLabel(student.urgency_level)}</p>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-orange-500 h-2 rounded-full"
                    style={{ width: `${(student.urgency_level / 5) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Learning History */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
              Learning History
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-500">Previous Tutoring Experience</span>
                <p className="text-base font-medium text-gray-900">
                  {student.previous_tutoring_experience || 0} sessions
                </p>
              </div>
              {student.previous_satisfaction && (
                <div>
                  <span className="text-sm text-gray-500">Previous Satisfaction</span>
                  <p className="text-base font-medium text-gray-900">
                    {formatScale(student.previous_satisfaction, 5)} - {getSatisfactionLabel(student.previous_satisfaction)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Learning Goals */}
          {student.learning_goals && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
                Learning Goals
              </h3>
              <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3">
                {student.learning_goals}
              </p>
            </div>
          )}

          {/* Additional Preferences */}
          {student.preferences_json && Object.keys(student.preferences_json).length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
                Additional Preferences
              </h3>
              <div className="bg-gray-50 rounded-lg p-3">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                  {JSON.stringify(student.preferences_json, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </Modal>
  )
}

export default StudentDetailModal

