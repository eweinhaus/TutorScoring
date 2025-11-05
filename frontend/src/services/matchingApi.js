/**
 * API client for matching service endpoints.
 */
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'
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
    if (error.response) {
      // Server responded with error
      const message = error.response.data?.detail || error.response.data?.error || 'An error occurred'
      return Promise.reject(new Error(message))
    } else if (error.request) {
      // Request made but no response
      return Promise.reject(new Error('No response from server. Please check your connection.'))
    } else {
      // Error setting up request
      return Promise.reject(new Error('Request setup error'))
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

