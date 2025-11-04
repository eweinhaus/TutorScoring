/**
 * Format a number as a percentage with 1 decimal place
 * @param {number|null|undefined} value - Value to format
 * @returns {string} Formatted percentage or 'N/A'
 */
export const formatPercentage = (value) => {
  if (value === null || value === undefined || isNaN(value)) {
    return 'N/A'
  }
  return `${parseFloat(value).toFixed(1)}%`
}

/**
 * Format a date as a readable date string
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date (e.g., "Jan 15, 2024")
 */
export const formatDate = (date) => {
  if (!date) return 'N/A'
  
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date
    return dateObj.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch (error) {
    return 'Invalid Date'
  }
}

/**
 * Format a date as a datetime string
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted datetime (e.g., "Jan 15, 2024 at 2:30 PM")
 */
export const formatDateTime = (date) => {
  if (!date) return 'N/A'
  
  try {
    const dateObj = typeof date === 'string' ? new Date(date) : date
    return dateObj.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    })
  } catch (error) {
    return 'Invalid Date'
  }
}

/**
 * Format hours as a readable string
 * @param {number|null|undefined} hours - Hours to format
 * @returns {string} Formatted hours (e.g., "12.5 hours")
 */
export const formatHours = (hours) => {
  if (hours === null || hours === undefined || isNaN(hours)) {
    return 'N/A'
  }
  const value = parseFloat(hours)
  return `${value.toFixed(1)} hours`
}

/**
 * Get color code for risk level based on rate and threshold
 * @param {number} rate - Reschedule rate percentage
 * @param {number} threshold - Risk threshold (default: 15)
 * @returns {string} Color name ('red', 'yellow', or 'green')
 */
export const getRiskColor = (rate, threshold = 15) => {
  // Handle null, undefined, empty string, or invalid values
  if (rate === null || rate === undefined || rate === '') {
    return 'gray'
  }
  
  // Convert to number, handle string values
  const value = parseFloat(rate)
  
  // Check if conversion resulted in NaN
  if (isNaN(value)) {
    return 'gray'
  }
  
  if (value >= threshold) {
    return 'red'
  }
  
  if (value >= threshold * 0.67) {
    return 'yellow'
  }
  
  return 'green'
}

