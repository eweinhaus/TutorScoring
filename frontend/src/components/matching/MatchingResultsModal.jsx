import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { getStudents, getTutors } from '../../services/matchingApi'
import Modal from '../common/Modal'
import { formatChurnProbability } from '../../utils/formatters'

function MatchingResultsModal({ isOpen, onClose, results }) {
  // Fetch students and tutors for name lookup
  const { data: studentsData } = useQuery({
    queryKey: ['students'],
    queryFn: () => getStudents(100, 0),
    enabled: isOpen && !!results,
  })

  const { data: tutorsData } = useQuery({
    queryKey: ['matching-tutors'],
    queryFn: () => getTutors(100, 0),
    enabled: isOpen && !!results,
  })

  if (!results || !results.matches || results.matches.length === 0) {
    return null
  }

  const students = studentsData?.students || []
  const tutors = tutorsData || []

  // Create lookup maps for names
  const studentMap = new Map(students.map(s => [s.id, s]))
  const tutorMap = new Map(tutors.map(t => [t.id, t]))


  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      title="Matching Results" 
      size="xl"
      headerClassName="p-6"
    >
      <div className="space-y-6">
        {/* Matched Pairs Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Student
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tutor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Churn Probability
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {results.matches.map((match, index) => {
                const student = studentMap.get(match.student_id)
                const tutor = tutorMap.get(match.tutor_id)
                const studentName = student?.name || 'Unknown'
                const tutorName = tutor?.name || 'Unknown'
                const churnProbability = parseFloat(match.churn_probability)

                return (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{studentName}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{tutorName}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {formatChurnProbability(churnProbability)}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </Modal>
  )
}

export default MatchingResultsModal

