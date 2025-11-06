import React, { useState } from 'react'
import StudentDetailModal from './StudentDetailModal'

function StudentList({ students, selectedId, selectedIds, onSelect, onToggleSelect }) {
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const [selectedStudentId, setSelectedStudentId] = useState(null)

  const handleViewDetails = (e, studentId) => {
    e.stopPropagation() // Prevent card selection
    setSelectedStudentId(studentId)
    setDetailModalOpen(true)
  }

  const handleCloseModal = () => {
    setDetailModalOpen(false)
    setSelectedStudentId(null)
  }

  const handleCardClick = (studentId) => {
    // If onToggleSelect is provided, use card click for multi-select
    // Otherwise, use for single-select compatibility modal
    if (onToggleSelect) {
      onToggleSelect(studentId)
    } else if (onSelect) {
      onSelect(studentId)
    }
  }

  return (
    <>
      <div className="space-y-2">
        {students.map((student) => {
          const isMultiSelected = selectedIds?.includes(student.id)
          const isSingleSelected = selectedId === student.id
          // Show blue border for single-select (compatibility modal), green for multi-select
          const borderClass = isSingleSelected 
            ? 'border-blue-500 bg-blue-50'
            : isMultiSelected
            ? 'border-green-400 bg-green-50'
            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
          
          return (
          <div
            key={student.id}
            onClick={() => handleCardClick(student.id)}
            className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${borderClass}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="font-medium">{student.name}</div>
                <div className="text-sm text-gray-600">
                  Age {student.age} • Pace {student.preferred_pace}/5 • {student.preferred_teaching_style}
                </div>
              </div>
              <button
                onClick={(e) => handleViewDetails(e, student.id)}
                className="ml-2 px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
                title="View full profile"
              >
                View Details
              </button>
            </div>
          </div>
          )
        })}
      </div>
      <StudentDetailModal
        studentId={selectedStudentId}
        isOpen={detailModalOpen}
        onClose={handleCloseModal}
      />
    </>
  )
}

export default StudentList

