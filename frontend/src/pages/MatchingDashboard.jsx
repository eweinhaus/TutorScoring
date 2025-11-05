import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getStudents, getTutors, getMatchPrediction } from '../services/matchingApi'
import StudentList from '../components/matching/StudentList'
import TutorList from '../components/matching/TutorList'
import MatchDetailPanel from '../components/matching/MatchDetailPanel'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorMessage from '../components/common/ErrorMessage'

/**
 * Matching Dashboard page for exploring student-tutor matches.
 */
function MatchingDashboard() {
  const [selectedStudentId, setSelectedStudentId] = useState(null)
  const [selectedTutorId, setSelectedTutorId] = useState(null)

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

  // Fetch match prediction when both selected
  const {
    data: matchPrediction,
    isLoading: matchLoading,
    error: matchError,
  } = useQuery({
    queryKey: ['match-prediction', selectedStudentId, selectedTutorId],
    queryFn: () => getMatchPrediction(selectedStudentId, selectedTutorId),
    enabled: !!selectedStudentId && !!selectedTutorId,
  })

  const students = studentsData?.students || []
  const tutors = tutorsData || []

  const handleStudentSelect = (studentId) => {
    setSelectedStudentId(studentId)
  }

  const handleTutorSelect = (tutorId) => {
    setSelectedTutorId(tutorId)
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Matching Dashboard</h1>
        <p className="text-gray-600">
          Select a student and tutor to view match predictions and compatibility analysis.
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Students column */}
          <div className="lg:col-span-1">
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
          <div className="lg:col-span-1">
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

          {/* Match detail panel */}
          <div className="lg:col-span-1">
            {selectedStudentId && selectedTutorId ? (
              <MatchDetailPanel
                studentId={selectedStudentId}
                tutorId={selectedTutorId}
                matchPrediction={matchPrediction}
                isLoading={matchLoading}
                error={matchError}
              />
            ) : (
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-gray-500 text-center py-8">
                  Select a student and tutor to view match details
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default MatchingDashboard

