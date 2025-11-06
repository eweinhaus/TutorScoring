import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getStudents, getTutors } from '../services/matchingApi'
import StudentList from '../components/matching/StudentList'
import TutorList from '../components/matching/TutorList'
import MatchDetailModal from '../components/matching/MatchDetailModal'
import MatchingAlgorithmModal from '../components/matching/MatchingAlgorithmModal'
import MatchingResultsModal from '../components/matching/MatchingResultsModal'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'

/**
 * Matching Dashboard page for exploring student-tutor matches.
 * Main page handles 1-to-1 comparison, with a button to open matching algorithm modal.
 */
function MatchingDashboard() {
  // Single-select for compatibility modal
  const [selectedStudentId, setSelectedStudentId] = useState(null)
  const [selectedTutorId, setSelectedTutorId] = useState(null)
  const [matchModalOpen, setMatchModalOpen] = useState(false)
  const [algorithmModalOpen, setAlgorithmModalOpen] = useState(false)
  const [resultsModalOpen, setResultsModalOpen] = useState(false)
  const [matchingResults, setMatchingResults] = useState(null)
  const [showLoadingForResults, setShowLoadingForResults] = useState(false)

  // Fetch students
  const {
    data: studentsData,
    isLoading: studentsLoading,
    error: studentsError,
  } = useQuery({
    queryKey: ['students'],
    queryFn: () => getStudents(500, 0),
  })

  // Fetch tutors
  const {
    data: tutorsData,
    isLoading: tutorsLoading,
    error: tutorsError,
  } = useQuery({
    queryKey: ['matching-tutors'],
    queryFn: () => getTutors(500, 0),
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

  // Open match modal when both student and tutor are selected
  useEffect(() => {
    if (selectedStudentId && selectedTutorId) {
      setMatchModalOpen(true)
    }
  }, [selectedStudentId, selectedTutorId])

  const handleStudentSelect = (studentId) => {
    setSelectedStudentId(studentId)
  }

  const handleTutorSelect = (tutorId) => {
    setSelectedTutorId(tutorId)
  }

  const handleCloseMatchModal = () => {
    setMatchModalOpen(false)
    // Optionally clear selections when modal closes
    // setSelectedStudentId(null)
    // setSelectedTutorId(null)
  }

  const handleResultsReady = async (results) => {
    setMatchingResults(results)
    setShowLoadingForResults(true)
    
    // Show loading for at least 0.75 seconds
    await new Promise(resolve => setTimeout(resolve, 750))
    
    setShowLoadingForResults(false)
    setResultsModalOpen(true)
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Matching Dashboard</h1>
            <p className="text-gray-600">
              Click on a student and tutor card to view match predictions and compatibility analysis.
            </p>
          </div>
          <button
            onClick={() => setAlgorithmModalOpen(true)}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 shadow-md transition-all"
          >
            Matching Algorithm
          </button>
        </div>
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Students column */}
          <div>
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-xl font-semibold mb-4">Students ({students.length})</h2>
              {students.length === 0 ? (
                <p className="text-gray-500">No students found.</p>
              ) : (
                <div className="max-h-[600px] overflow-y-auto">
                  <StudentList
                    students={students}
                    selectedId={selectedStudentId}
                    onSelect={handleStudentSelect}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Tutors column */}
          <div>
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-xl font-semibold mb-4">Tutors ({tutors.length})</h2>
              {tutors.length === 0 ? (
                <div className="text-gray-500">
                  <p>No tutors with survey data found.</p>
                  {tutorsRaw.length > 0 && (
                    <p className="text-xs text-gray-400 mt-1">
                      ({tutorsRaw.length} tutors without survey data were filtered out)
                    </p>
                  )}
                </div>
              ) : (
                <div className="max-h-[600px] overflow-y-auto">
                  <TutorList
                    tutors={tutors}
                    selectedId={selectedTutorId}
                    onSelect={handleTutorSelect}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Match Detail Modal */}
      <MatchDetailModal
        studentId={selectedStudentId}
        tutorId={selectedTutorId}
        isOpen={matchModalOpen}
        onClose={handleCloseMatchModal}
      />

      {/* Matching Algorithm Modal */}
      <MatchingAlgorithmModal
        isOpen={algorithmModalOpen}
        onClose={() => setAlgorithmModalOpen(false)}
        onResultsReady={handleResultsReady}
      />

      {/* Loading overlay for matching results */}
      {showLoadingForResults && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg p-8 shadow-xl">
            <LoadingSpinner message="Processing matching results..." size="large" />
          </div>
        </div>
      )}

      {/* Matching Results Modal */}
      <MatchingResultsModal
        isOpen={resultsModalOpen}
        onClose={() => {
          setResultsModalOpen(false)
          setMatchingResults(null)
        }}
        results={matchingResults}
      />
    </div>
  )
}

export default MatchingDashboard

