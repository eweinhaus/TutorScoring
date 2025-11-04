import React, { useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { formatPercentage } from '../../utils/formatters'

/**
 * Reschedule rate chart component showing trends over time
 * @param {Array} data - Chart data array with date and rates
 * @param {number} threshold - Risk threshold line value
 * @param {string} timePeriod - Selected time period (7d, 30d, 90d)
 */
function RescheduleRateChart({ data = [], threshold = 15, timePeriod = '30d' }) {
  // Transform data for chart
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return []

    // Group data by date if needed
    // Assuming data is already in the correct format: [{ date, rate7d, rate30d, rate90d }]
    return data.map((item) => ({
      date: new Date(item.date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
      '7d Rate': item.rate7d || item.reschedule_rate_7d || 0,
      '30d Rate': item.rate30d || item.reschedule_rate_30d || 0,
      '90d Rate': item.rate90d || item.reschedule_rate_90d || 0,
    }))
  }, [data])

  if (!data || data.length === 0) {
    return (
      <div className="card">
        <p className="text-center text-gray-500 py-8">No chart data available</p>
      </div>
    )
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
          <p className="font-medium mb-2">{label}</p>
          {payload.map((entry, index) => (
            <p
              key={index}
              className="text-sm"
              style={{ color: entry.color }}
            >
              {`${entry.name}: ${formatPercentage(entry.value)}`}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4">Reschedule Rate Trends</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            stroke="#6b7280"
            tick={{ fill: '#6b7280' }}
          />
          <YAxis
            stroke="#6b7280"
            tick={{ fill: '#6b7280' }}
            domain={[0, 100]}
            label={{
              value: 'Percentage (%)',
              angle: -90,
              position: 'insideLeft',
              style: { textAnchor: 'middle', fill: '#6b7280' },
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <ReferenceLine
            y={threshold}
            stroke="#ef4444"
            strokeDasharray="5 5"
            label={{ value: `${threshold}% Threshold`, position: 'topRight' }}
          />
          <Line
            type="monotone"
            dataKey="7d Rate"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="30d Rate"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="90d Rate"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default RescheduleRateChart

