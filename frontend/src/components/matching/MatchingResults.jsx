import React from 'react'
import { formatChurnProbability } from '../../utils/formatters'

function MatchingResults({ results, students, tutors }) {
  if (!results || !results.matches || results.matches.length === 0) {
    return null
  }

  // Create lookup maps for names
  const studentMap = new Map(students.map(s => [s.id, s]))
  const tutorMap = new Map(tutors.map(t => [t.id, t]))

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case 'low':
        return 'bg-green-100 text-green-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'high':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatPercent = (value) => {
    return (value * 100).toFixed(1) + '%'
  }

  return (
    <div className="mt-6 bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Matching Results</h2>
      
      {/* Summary Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Total Churn Risk</div>
          <div className="text-2xl font-bold text-gray-900">{formatPercent(results.total_churn_risk)}</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Avg Churn Risk</div>
          <div className="text-2xl font-bold text-gray-900">{formatPercent(results.avg_churn_risk)}</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Total Compatibility</div>
          <div className="text-2xl font-bold text-green-600">{formatPercent(results.total_compatibility)}</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-600">Avg Compatibility</div>
          <div className="text-2xl font-bold text-green-600">{formatPercent(results.avg_compatibility)}</div>
        </div>
      </div>

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
                Risk Level
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Churn Probability
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Compatibility
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {results.matches.map((match, index) => {
              const student = studentMap.get(match.student_id)
              const tutor = tutorMap.get(match.tutor_id)
              const studentName = student?.name || 'Unknown'
              const tutorName = tutor?.name || 'Unknown'

              return (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{studentName}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{tutorName}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getRiskColor(match.risk_level)}`}>
                      {match.risk_level}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{formatChurnProbability(match.churn_probability)}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="text-sm text-gray-900 mr-2">{formatPercent(match.compatibility_score)}</div>
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{ width: `${match.compatibility_score * 100}%` }}
                        />
                      </div>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default MatchingResults

