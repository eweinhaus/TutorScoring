import React, { lazy, Suspense } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/common/Layout'
import LoadingSpinner from './components/common/LoadingSpinner'

// Lazy load pages for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'))
const TutorList = lazy(() => import('./pages/TutorList'))
const TutorDetail = lazy(() => import('./pages/TutorDetail'))

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
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
