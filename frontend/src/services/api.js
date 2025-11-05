import axios from 'axios'

// Use CloudFront URL for API (which proxies to ALB)
// This ensures all requests go through HTTPS
const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  
  // In production, use CloudFront URL (same domain as frontend)
  // CloudFront will proxy /api/* requests to ALB
  if (import.meta.env.PROD) {
    // Use relative URL or same CloudFront domain
    return window.location.origin
  }
  
  return 'http://localhost:8001'
}

const API_BASE_URL = getApiUrl()
const API_KEY = import.meta.env.VITE_API_KEY

// Log API key status in development (without exposing the actual key)
if (import.meta.env.DEV) {
  if (API_KEY) {
    console.log('[API] API key configured (length:', API_KEY.length, ')')
  } else {
    console.warn('[API] VITE_API_KEY not set - API key header will not be sent')
  }
}

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
    ...(API_KEY && { 'X-API-Key': API_KEY }),
  },
})

// Request interceptor for logging (dev only)
apiClient.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      const hasApiKey = config.headers['X-API-Key'] || config.headers['x-api-key']
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, {
        hasApiKey: !!hasApiKey,
        ...(config.params || config.data ? { data: config.params || config.data } : {})
      })
      if (!hasApiKey && !API_KEY) {
        console.warn(`[API] Warning: No API key header will be sent. Set VITE_API_KEY environment variable.`)
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Handle network errors
    if (!error.response) {
      error.message = 'Unable to connect to server. Please check your connection.'
      return Promise.reject(error)
    }

    // Handle HTTP errors
    const status = error.response?.status
    const data = error.response?.data

    switch (status) {
      case 401:
        if (data?.detail) {
          error.message = data.detail
        } else {
          error.message = 'Unauthorized. Please check your API key. Make sure VITE_API_KEY is set in your environment variables.'
        }
        break
      case 404:
        error.message = data?.detail || 'Resource not found.'
        break
      case 400:
        error.message = data?.detail || 'Invalid request. Please check your input.'
        break
      case 500:
        error.message = 'Server error. Please try again later.'
        break
      default:
        error.message = data?.detail || 'Something went wrong. Please try again.'
    }

    return Promise.reject(error)
  }
)

/**
 * Get list of tutors with optional filters
 * @param {Object} filters - Filter options
 * @param {string} filters.risk_status - Filter by risk status (high_risk, low_risk, all)
 * @param {string} filters.sort_by - Sort field (reschedule_rate_30d, total_sessions_30d, name)
 * @param {string} filters.sort_order - Sort order (asc, desc)
 * @param {number} filters.limit - Number of results per page
 * @param {number} filters.offset - Offset for pagination
 * @returns {Promise<Object>} Response data
 */
export const getTutors = async (filters = {}) => {
  const response = await apiClient.get('/tutors', { params: filters })
  return response.data
}

/**
 * Get tutor details by ID
 * @param {string} id - Tutor ID
 * @returns {Promise<Object>} Tutor data
 */
export const getTutor = async (id) => {
  const response = await apiClient.get(`/tutors/${id}`)
  return response.data
}

/**
 * Get tutor reschedule history
 * @param {string} id - Tutor ID
 * @param {number} days - Number of days to look back (default: 90)
 * @returns {Promise<Object>} History data
 */
export const getTutorHistory = async (id, days = 90) => {
  const response = await apiClient.get(`/tutors/${id}/history`, {
    params: { days },
  })
  return response.data
}

/**
 * Create a new session (for testing)
 * @param {Object} sessionData - Session data
 * @returns {Promise<Object>} Created session data
 */
export const createSession = async (sessionData) => {
  const response = await apiClient.post('/sessions', sessionData)
  return response.data
}

export default apiClient
