import React from 'react'

function StudentList({ students, selectedId, onSelect }) {
  return (
    <div className="space-y-2">
      {students.map((student) => (
        <div
          key={student.id}
          onClick={() => onSelect(student.id)}
          className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
            selectedId === student.id
              ? 'border-primary bg-primary/10'
              : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
          }`}
        >
          <div className="font-medium">{student.name}</div>
          <div className="text-sm text-gray-600">
            Age {student.age} • Pace {student.preferred_pace}/5 • {student.preferred_teaching_style}
          </div>
        </div>
      ))}
    </div>
  )
}

export default StudentList

