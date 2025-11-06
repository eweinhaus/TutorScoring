import apiClient from './api'

/**
 * Get upcoming sessions with reschedule predictions
 * @param {Object} params - Query parameters
 * @param {number} params.days_ahead - Number of days ahead to show (default: 7)
 * @param {string} params.risk_level - Filter by risk level (low/medium/high)
 * @param {string} params.tutor_id - Filter by tutor ID
 * @param {number} params.limit - Pagination limit (default: 50)
 * @param {number} params.offset - Pagination offset (default: 0)
 * @param {string} params.sort_by - Sort field (scheduled_time, reschedule_probability, tutor_name, student_id)
 * @param {string} params.sort_order - Sort order (asc, desc)
 * @returns {Promise<Object>} Response data with sessions array
 */
export const getUpcomingSessions = async (params = {}) => {
  const response = await apiClient.get('/upcoming-sessions', { params })
  return response.data
}

/**
 * Get or refresh reschedule prediction for a specific session
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} Prediction data
 */
export const getSessionPrediction = async (sessionId) => {
  const response = await apiClient.get(`/upcoming-sessions/${sessionId}/predict`)
  return response.data
}

/**
 * Batch generate predictions for multiple sessions
 * @param {Object} options - Batch options
 * @param {Array<string>} options.session_ids - Array of session IDs (optional)
 * @param {number} options.days_ahead - Number of days ahead to predict (optional)
 * @returns {Promise<Object>} Summary of predictions
 */
export const batchPredictSessions = async (options = {}) => {
  const response = await apiClient.post('/upcoming-sessions/batch-predict', options)
  return response.data
}

