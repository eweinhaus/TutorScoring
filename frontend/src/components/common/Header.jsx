import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

/**
 * Header component with navigation
 */
function Header() {
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const isActive = (path) => {
    return location.pathname === path
  }

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Title */}
          <Link to="/" className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-primary">Tutor Quality Scoring</h1>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            <Link
              to="/tutors"
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/tutors')
                  ? 'bg-primary text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              Tutors
            </Link>
            <Link
              to="/matching"
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/matching')
                  ? 'bg-primary text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              Matching
            </Link>
            <Link
              to="/upcoming-sessions"
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/upcoming-sessions')
                  ? 'bg-primary text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              Upcoming Sessions
            </Link>
          </nav>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 rounded-md text-gray-700 hover:bg-gray-100"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              {mobileMenuOpen ? (
                <path d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-200">
            <Link
              to="/tutors"
              className={`block px-3 py-2 rounded-md text-base font-medium ${
                isActive('/tutors')
                  ? 'bg-primary text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              Tutors
            </Link>
            <Link
              to="/matching"
              className={`block px-3 py-2 rounded-md text-base font-medium ${
                isActive('/matching')
                  ? 'bg-primary text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              Matching
            </Link>
            <Link
              to="/upcoming-sessions"
              className={`block px-3 py-2 rounded-md text-base font-medium ${
                isActive('/upcoming-sessions')
                  ? 'bg-primary text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              Upcoming Sessions
            </Link>
          </div>
        )}
      </div>
    </header>
  )
}

export default Header

