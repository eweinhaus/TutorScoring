import React from 'react'

function TutorList({ tutors, selectedId, onSelect }) {
  return (
    <div className="space-y-2">
      {tutors.map((tutor) => (
        <div
          key={tutor.id}
          onClick={() => onSelect(tutor.id)}
          className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
            selectedId === tutor.id
              ? 'border-primary bg-primary/10'
              : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
          }`}
        >
          <div className="font-medium">{tutor.name}</div>
          <div className="text-sm text-gray-600">
            {tutor.experience_years ? `${tutor.experience_years} years exp` : 'New tutor'} • {tutor.teaching_style || 'N/A'}
          </div>
        </div>
      ))}
    </div>
  )
}

export default TutorList

