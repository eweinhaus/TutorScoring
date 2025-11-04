import React from 'react'

/**
 * Loading spinner component
 * @param {string} size - Size of spinner (small, medium, large)
 * @param {string} message - Optional loading message
 */
function LoadingSpinner({ size = 'medium', message }) {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8',
    large: 'w-12 h-12',
  }

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div
        className={`${sizeClasses[size]} border-4 border-primary border-t-transparent rounded-full animate-spin`}
        role="status"
        aria-label="Loading"
      >
        <span className="sr-only">Loading...</span>
      </div>
      {message && (
        <p className="mt-4 text-gray-600 text-sm">{message}</p>
      )}
    </div>
  )
}

export default LoadingSpinner

