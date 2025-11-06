/**
 * Risk threshold for high-risk tutors (percentage)
 */
export const RISK_THRESHOLD = 15

/**
 * Warning threshold for tutors approaching high-risk (percentage)
 */
export const WARNING_THRESHOLD = 10

/**
 * Available time period options
 */
export const TIME_PERIODS = ['7d', '30d', '90d']

/**
 * Risk status filter options
 */
export const RISK_STATUS = {
  HIGH: 'high_risk',
  LOW: 'low_risk',
  ALL: 'all',
}

/**
 * Sort options for tutor list
 */
export const SORT_OPTIONS = {
  RESCHEDULE_RATE: 'reschedule_rate_30d',
  TOTAL_SESSIONS: 'total_sessions_30d',
  NAME: 'name',
}

/**
 * Sort order options
 */
export const SORT_ORDER = {
  ASC: 'asc',
  DESC: 'desc',
}

/**
 * API endpoints (for reference)
 */
export const API_ENDPOINTS = {
  TUTORS: '/tutors',
  TUTOR_DETAIL: '/tutors/:id',
  TUTOR_HISTORY: '/tutors/:id/history',
  SESSIONS: '/sessions',
  HEALTH: '/health',
}

/**
 * Default pagination values
 */
export const DEFAULT_PAGE_SIZE = 20

/**
 * Reschedule risk levels
 */
export const RESCHEDULE_RISK_LEVELS = ['low', 'medium', 'high']

/**
 * Days ahead options for upcoming sessions
 */
export const DAYS_AHEAD_OPTIONS = [7, 14, 30]

/**
 * Sort options for upcoming sessions
 */
export const UPCOMING_SESSIONS_SORT_OPTIONS = {
  SCHEDULED_TIME: 'scheduled_time',
  RESCHEDULE_PROBABILITY: 'reschedule_probability',
  TUTOR_NAME: 'tutor_name',
  STUDENT_ID: 'student_id',
}

