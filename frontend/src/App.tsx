import './index.css'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { ActiveJobsProvider } from './contexts/ActiveJobsContext'
import { AuthProvider } from './contexts/AuthContext'
import { Navbar } from './components/Navbar'
import { LandingNavbar } from './components/landing/LandingNavbar'
import { Dashboard } from './pages/Dashboard'
import { Settings } from './pages/Settings'
import { Analytics } from './pages/Analytics'
import { DeckBuilder } from './pages/DeckBuilder'
import Login from './pages/Login'
import AuthCallback from './pages/AuthCallback'
import ProtectedRoute from './components/ProtectedRoute'

const Landing = lazy(() => import('./pages/Landing').then(m => ({ default: m.Landing })))

function AppContent() {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';
  const isLandingPage = location.pathname === '/';

  return (
    <>
      {isLandingPage && <LandingNavbar />}
      {!isLandingPage && !isLoginPage && <Navbar />}
      <Routes>
        <Route
          path="/"
          element={
            <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
              <Landing />
            </Suspense>
          }
        />
        <Route path="/login" element={<Login />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <Analytics />
            </ProtectedRoute>
          }
        />
        <Route
          path="/decks"
          element={
            <ProtectedRoute>
              <DeckBuilder />
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ActiveJobsProvider>
          <AppContent />
        </ActiveJobsProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
