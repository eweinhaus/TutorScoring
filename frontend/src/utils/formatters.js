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
 * Format churn probability with special handling for extreme values
 * @param {number|string} probability - Churn probability (0-1 or percentage 0-100)
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {string} Formatted churn probability (e.g., "<2%", ">98%", "23.5%")
 */
export const formatChurnProbability = (probability, decimals = 1) => {
  if (probability === null || probability === undefined || probability === '') {
    return 'N/A'
  }
  
  // Convert to number (handle both 0-1 and 0-100 formats)
  let value = parseFloat(probability)
  
  // If value is > 1, assume it's already a percentage (0-100), otherwise assume 0-1
  if (value > 1) {
    value = value / 100
  }
  
  // Check if conversion resulted in NaN
  if (isNaN(value)) {
    return 'N/A'
  }
  
  // Clamp value to 0-1 range
  value = Math.max(0, Math.min(1, value))
  
  // Convert to percentage
  const percent = value * 100
  
  // Handle extreme values
  if (percent < 2) {
    return '<2%'
  }
  
  if (percent > 98) {
    return '>98%'
  }
  
  // Return formatted percentage with specified decimals
  return `${percent.toFixed(decimals)}%`
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

