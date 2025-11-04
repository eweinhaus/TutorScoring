import React from 'react'

/**
 * Error message component with optional retry functionality
 * @param {Error|string} error - Error object or error message
 * @param {Function} onRetry - Optional retry callback
 */
function ErrorMessage({ error, onRetry }) {
  // Extract error message
  let errorMessage = 'Something went wrong. Please try again.'
  
  if (typeof error === 'string') {
    errorMessage = error
  } else if (error?.message) {
    errorMessage = error.message
  } else if (error?.response?.data?.detail) {
    errorMessage = error.response.data.detail
  }

  // Determine error type for better messaging
  if (errorMessage.includes('connect') || errorMessage.includes('network')) {
    errorMessage = 'Unable to connect to server. Please check your connection.'
  } else if (errorMessage.includes('not found') || errorMessage.includes('404')) {
    errorMessage = 'Resource not found.'
  } else if (errorMessage.includes('401') || errorMessage.includes('Unauthorized')) {
    errorMessage = 'Unauthorized. Please check your API key.'
  }

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg
            className="h-5 w-5 text-red-400"
            fill="currentColor"
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">Error</h3>
          <p className="mt-1 text-sm text-red-700">{errorMessage}</p>
          {onRetry && (
            <div className="mt-4">
              <button
                onClick={onRetry}
                className="btn btn-primary text-sm"
              >
                Retry
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ErrorMessage

