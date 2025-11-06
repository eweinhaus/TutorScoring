import React, { useState } from 'react'
import TutorDetailModal from './TutorDetailModal'

function TutorList({ tutors, selectedId, selectedIds, onSelect, onToggleSelect }) {
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const [selectedTutorId, setSelectedTutorId] = useState(null)

  const handleViewDetails = (e, tutorId) => {
    e.stopPropagation() // Prevent card selection
    setSelectedTutorId(tutorId)
    setDetailModalOpen(true)
  }

  const handleCloseModal = () => {
    setDetailModalOpen(false)
    setSelectedTutorId(null)
  }

  const handleCardClick = (tutorId) => {
    // If onToggleSelect is provided, use card click for multi-select
    // Otherwise, use for single-select compatibility modal
    if (onToggleSelect) {
      onToggleSelect(tutorId)
    } else if (onSelect) {
      onSelect(tutorId)
    }
  }

  return (
    <>
      <div className="space-y-2">
        {tutors.map((tutor) => {
          const isMultiSelected = selectedIds?.includes(tutor.id)
          const isSingleSelected = selectedId === tutor.id
          // Show blue border for single-select (compatibility modal), green for multi-select
          const borderClass = isSingleSelected 
            ? 'border-blue-500 bg-blue-50'
            : isMultiSelected
            ? 'border-green-400 bg-green-50'
            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
          
          return (
          <div
            key={tutor.id}
            onClick={() => handleCardClick(tutor.id)}
            className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${borderClass}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="font-medium">{tutor.name}</div>
                <div className="text-sm text-gray-600">
                  {tutor.experience_years ? `${tutor.experience_years} years exp` : 'New tutor'} • {tutor.teaching_style || 'N/A'}
                </div>
              </div>
              <button
                onClick={(e) => handleViewDetails(e, tutor.id)}
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
      <TutorDetailModal
        tutorId={selectedTutorId}
        isOpen={detailModalOpen}
        onClose={handleCloseModal}
      />
    </>
  )
}

export default TutorList

