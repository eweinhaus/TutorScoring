import React, { lazy, Suspense } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Layout from './components/common/Layout'
import LoadingSpinner from './components/common/LoadingSpinner'

// Lazy load pages for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'))
const TutorList = lazy(() => import('./pages/TutorList'))
const TutorDetail = lazy(() => import('./pages/TutorDetail'))
const MatchingDashboard = lazy(() => import('./pages/MatchingDashboard'))
const UpcomingSessions = lazy(() => import('./pages/UpcomingSessions'))

// Create QueryClient instance outside component to avoid recreating on re-renders
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // 30 seconds
      refetchOnWindowFocus: false,
      retry: 3,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route
              index
              element={
                <Suspense fallback={<LoadingSpinner message="Loading dashboard..." />}>
                  <Dashboard />
                </Suspense>
              }
            />
            <Route
              path="tutors"
              element={
                <Suspense fallback={<LoadingSpinner message="Loading tutors..." />}>
                  <TutorList />
                </Suspense>
              }
            />
            <Route
              path="tutors/:id"
              element={
                <Suspense fallback={<LoadingSpinner message="Loading tutor details..." />}>
                  <TutorDetail />
                </Suspense>
              }
            />
            <Route
              path="matching"
              element={
                <Suspense fallback={<LoadingSpinner message="Loading matching dashboard..." />}>
                  <MatchingDashboard />
                </Suspense>
              }
            />
            <Route
              path="upcoming-sessions"
              element={
                <Suspense fallback={<LoadingSpinner message="Loading upcoming sessions..." />}>
                  <UpcomingSessions />
                </Suspense>
              }
            />
            <Route
              path="*"
              element={
                <div className="card">
                  <h2 className="text-xl font-semibold mb-4">Page Not Found</h2>
                  <p className="text-gray-600 mb-4">
                    The page you're looking for doesn't exist.
                  </p>
                  <Link to="/" className="btn btn-primary">
                    Go to Dashboard
                  </Link>
                </div>
              }
            />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
