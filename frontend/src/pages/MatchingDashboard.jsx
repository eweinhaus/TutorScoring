import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getStudents, getTutors } from '../services/matchingApi'
import StudentList from '../components/matching/StudentList'
import TutorList from '../components/matching/TutorList'
import MatchDetailModal from '../components/matching/MatchDetailModal'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'

/**
 * Matching Dashboard page for exploring student-tutor matches.
 */
function MatchingDashboard() {
  const [selectedStudentId, setSelectedStudentId] = useState(null)
  const [selectedTutorId, setSelectedTutorId] = useState(null)
  const [matchModalOpen, setMatchModalOpen] = useState(false)

  // Fetch students
  const {
    data: studentsData,
    isLoading: studentsLoading,
    error: studentsError,
  } = useQuery({
    queryKey: ['students'],
    queryFn: () => getStudents(100, 0),
  })

  // Fetch tutors
  const {
    data: tutorsData,
    isLoading: tutorsLoading,
    error: tutorsError,
  } = useQuery({
    queryKey: ['matching-tutors'],
    queryFn: () => getTutors(100, 0),
  })

  const students = studentsData?.students || []
  const tutors = tutorsData || []

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

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Matching Dashboard</h1>
        <p className="text-gray-600">
          Select a student and tutor to view match predictions and compatibility analysis. The match details will open in a popup.
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Students column */}
          <div>
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-xl font-semibold mb-4">Students</h2>
              {students.length === 0 ? (
                <p className="text-gray-500">No students found.</p>
              ) : (
                <StudentList
                  students={students}
                  selectedId={selectedStudentId}
                  onSelect={handleStudentSelect}
                />
              )}
            </div>
          </div>

          {/* Tutors column */}
          <div>
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-xl font-semibold mb-4">Tutors</h2>
              {tutors.length === 0 ? (
                <p className="text-gray-500">No tutors found.</p>
              ) : (
                <TutorList
                  tutors={tutors}
                  selectedId={selectedTutorId}
                  onSelect={handleTutorSelect}
                />
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
    </div>
  )
}

export default MatchingDashboard

