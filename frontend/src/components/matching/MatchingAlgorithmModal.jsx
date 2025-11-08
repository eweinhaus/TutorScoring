import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getStudents, getTutors, runMatching } from '../../services/matchingApi'
import StudentList from './StudentList'
import TutorList from './TutorList'
import Modal from '../common/Modal'
import LoadingSpinner from '../common/LoadingSpinner'
import ErrorMessage from '../common/ErrorMessage'

/**
 * Modal for running the matching algorithm with multi-select functionality.
 */
function MatchingAlgorithmModal({ isOpen, onClose, onResultsReady }) {
  const [selectedStudentIds, setSelectedStudentIds] = useState([])
  const [selectedTutorIds, setSelectedTutorIds] = useState([])
  const [matchingLoading, setMatchingLoading] = useState(false)
  const [matchingError, setMatchingError] = useState(null)

  // Fetch students
  const {
    data: studentsData,
    isLoading: studentsLoading,
    error: studentsError,
  } = useQuery({
    queryKey: ['students'],
    queryFn: () => getStudents(500, 0),
    enabled: isOpen,
  })

  // Fetch tutors
  const {
    data: tutorsData,
    isLoading: tutorsLoading,
    error: tutorsError,
  } = useQuery({
    queryKey: ['matching-tutors'],
    queryFn: () => getTutors(500, 0),
    enabled: isOpen,
  })

  const students = studentsData?.students || []
  // API returns array directly (not wrapped in object)
  const tutorsRaw = Array.isArray(tutorsData) ? tutorsData : []
  
  // Filter out tutors that don't have survey data (matching preferences)
  // Tutors need at least teaching_style to be useful for matching
  const tutors = tutorsRaw.filter(tutor => {
    if (!tutor) return false
    // Check if tutor has at least teaching_style (required for matching)
    // This prevents showing "New tutor N/A" in the UI
    const hasTeachingStyle = tutor.teaching_style != null && tutor.teaching_style !== ''
    return hasTeachingStyle
  })

  // Multi-select handlers
  const handleToggleStudent = (studentId) => {
    setSelectedStudentIds(prev => {
      if (prev.includes(studentId)) {
        return prev.filter(id => id !== studentId)
      } else {
        return [...prev, studentId]
      }
    })
  }

  const handleToggleTutor = (tutorId) => {
    setSelectedTutorIds(prev => {
      if (prev.includes(tutorId)) {
        return prev.filter(id => id !== tutorId)
      } else {
        return [...prev, tutorId]
      }
    })
  }

  const handleRunMatching = async () => {
    if (selectedStudentIds.length !== selectedTutorIds.length || selectedStudentIds.length < 2) {
      return
    }

    setMatchingLoading(true)
    setMatchingError(null)

    try {
      console.log('Running matching with:', { 
        students: selectedStudentIds.length, 
        tutors: selectedTutorIds.length 
      })
      const results = await runMatching(selectedStudentIds, selectedTutorIds)
      console.log('Matching results:', results)
      // Close this modal and pass results to parent
      handleClose()
      if (onResultsReady) {
        onResultsReady(results)
      }
    } catch (error) {
      console.error('Matching error:', error)
      setMatchingError(error.message || 'Failed to run matching algorithm')
    } finally {
      setMatchingLoading(false)
    }
  }

  const handleClose = () => {
    // Reset state when closing
    setSelectedStudentIds([])
    setSelectedTutorIds([])
    setMatchingError(null)
    onClose()
  }

  const canRunMatching = selectedStudentIds.length === selectedTutorIds.length && selectedStudentIds.length >= 2

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Matching Algorithm" size="xl">
      <div className="space-y-6">
        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-gray-700">
            Click on student and tutor cards to select them. The number of students and tutors must match, and you need at least 2 of each to run the algorithm.
          </p>
        </div>

        {/* Loading state */}
        {(studentsLoading || tutorsLoading) && (
          <LoadingSpinner message="Loading students and tutors..." />
        )}

        {/* Error state */}
        {(studentsError || tutorsError) && (
          <ErrorMessage
            message={studentsError?.message || tutorsError?.message || 'Failed to load data'}
          />
        )}

        {/* Main content */}
        {!studentsLoading && !tutorsLoading && !studentsError && !tutorsError && (
          <>
            {/* Selection counter and Run button */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-6">
                  <div className={`text-sm ${selectedStudentIds.length === selectedTutorIds.length && selectedStudentIds.length >= 2 ? 'text-green-600 font-semibold' : 'text-gray-600'}`}>
                    Students selected: <span className="font-bold">{selectedStudentIds.length}</span>
                  </div>
                  <div className={`text-sm ${selectedStudentIds.length === selectedTutorIds.length && selectedStudentIds.length >= 2 ? 'text-green-600 font-semibold' : 'text-gray-600'}`}>
                    Tutors selected: <span className="font-bold">{selectedTutorIds.length}</span>
                  </div>
                  {selectedStudentIds.length !== selectedTutorIds.length && (
                    <div className="text-sm text-amber-600">
                      {selectedStudentIds.length > selectedTutorIds.length 
                        ? 'Select more tutors'
                        : 'Select more students'}
                    </div>
                  )}
                </div>
                <button
                  onClick={handleRunMatching}
                  disabled={!canRunMatching || matchingLoading}
                  className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                    canRunMatching && !matchingLoading
                      ? 'bg-blue-600 text-white hover:bg-blue-700 hover:text-white shadow-md'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  {matchingLoading ? 'Running Algorithm...' : 'Run Matching Algorithm'}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Students column */}
              <div>
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold mb-4">Students</h3>
                  {students.length === 0 ? (
                    <p className="text-gray-500">No students found.</p>
                  ) : (
                    <div className="max-h-96 overflow-y-auto">
                      <StudentList
                        students={students}
                        selectedIds={selectedStudentIds}
                        onToggleSelect={handleToggleStudent}
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Tutors column */}
              <div>
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h3 className="text-lg font-semibold mb-4">Tutors</h3>
                  {tutors.length === 0 ? (
                    <p className="text-gray-500">No tutors found.</p>
                  ) : (
                    <div className="max-h-96 overflow-y-auto">
                      <TutorList
                        tutors={tutors}
                        selectedIds={selectedTutorIds}
                        onToggleSelect={handleToggleTutor}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Matching error */}
            {matchingError && (
              <div>
                <ErrorMessage message={matchingError} />
              </div>
            )}
          </>
        )}
      </div>
    </Modal>
  )
}

export default MatchingAlgorithmModal

