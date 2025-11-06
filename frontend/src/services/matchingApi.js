/**
 * API client for matching service endpoints.
 */
import axios from 'axios'

// Always use relative URLs in production to ensure same-origin requests
// This works with CloudFront which proxies /api/* to ALB
const getApiUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  
  // In production, always use relative URL (same domain as frontend)
  // This ensures all requests go through HTTPS CloudFront
  if (import.meta.env.PROD) {
    // Use empty string for relative URLs, or window.location.origin
    return ''  // Empty string means relative to current origin
  }
  
  return '' // Use relative URL to go through vite proxy
}

const API_URL = getApiUrl()
const API_KEY = import.meta.env.VITE_API_KEY || ''

// Create axios instance
const apiClient = axios.create({
  baseURL: `${API_URL}/api/matching`,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
})

// Request interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    if (error.response) {
      // Server responded with error
      const message = error.response.data?.detail || error.response.data?.error || error.response.statusText || 'An error occurred'
      console.error('API Error Response:', error.response.data)
      return Promise.reject(new Error(message))
    } else if (error.request) {
      // Request made but no response
      console.error('No response from server:', error.request)
      return Promise.reject(new Error('No response from server. Please check your connection.'))
    } else {
      // Error setting up request
      console.error('Request setup error:', error.message)
      return Promise.reject(new Error(error.message || 'Request setup error'))
    }
  }
)

/**
 * Student API methods
 */
export const getStudents = async (limit = 100, offset = 0) => {
  const response = await apiClient.get('/students', {
    params: { limit, offset },
  })
  return response.data
}

export const getStudent = async (studentId) => {
  const response = await apiClient.get(`/students/${studentId}`)
  return response.data
}

export const createStudent = async (studentData) => {
  const response = await apiClient.post('/students', studentData)
  return response.data
}

/**
 * Tutor API methods (with preferences)
 */
export const getTutors = async (limit = 100, offset = 0) => {
  const response = await apiClient.get('/tutors', {
    params: { limit, offset },
  })
  return response.data
}

export const getTutor = async (tutorId) => {
  const response = await apiClient.get(`/tutors/${tutorId}`)
  return response.data
}

export const updateTutor = async (tutorId, tutorData) => {
  const response = await apiClient.patch(`/tutors/${tutorId}`, tutorData)
  return response.data
}

/**
 * Match prediction API methods
 */
export const getMatchPrediction = async (studentId, tutorId) => {
  const response = await apiClient.get(`/predict/${studentId}/${tutorId}`)
  return response.data
}

export const generateAllMatches = async () => {
  const response = await apiClient.post('/generate-all')
  return response.data
}

export const getStudentMatches = async (studentId, sortBy = 'compatibility_score', sortOrder = 'desc', limit = 100, offset = 0) => {
  const response = await apiClient.get(`/students/${studentId}/matches`, {
    params: { sort_by: sortBy, sort_order: sortOrder, limit, offset },
  })
  return response.data
}

export const getTutorMatches = async (tutorId, sortBy = 'compatibility_score', sortOrder = 'desc', limit = 100, offset = 0) => {
  const response = await apiClient.get(`/tutors/${tutorId}/matches`, {
    params: { sort_by: sortBy, sort_order: sortOrder, limit, offset },
  })
  return response.data
}

/**
 * Run matching algorithm to find optimal 1-to-1 assignments
 */
export const runMatching = async (studentIds, tutorIds) => {
  const response = await apiClient.post('/run-matching', {
    student_ids: studentIds,
    tutor_ids: tutorIds
  })
  return response.data
}

