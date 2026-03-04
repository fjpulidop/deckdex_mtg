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
import AdminRoute from './components/AdminRoute'
import { JobsBottomBar } from './components/JobsBottomBar'
import Import from './pages/Import'
import { Admin } from './pages/Admin'
import { Demo } from './pages/Demo'

const Landing = lazy(() => import('./pages/Landing').then(m => ({ default: m.Landing })))

function AppContent() {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';
  const isLandingPage = location.pathname === '/';
  const isDemoPage = location.pathname === '/demo';

  return (
    <>
      {isLandingPage && <LandingNavbar />}
      {!isLandingPage && !isLoginPage && !isDemoPage && <Navbar />}
      <Routes>
        <Route
          path="/"
          element={
            <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
              <Landing />
            </Suspense>
          }
        />
        <Route path="/demo" element={<Demo />} />
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
        <Route
          path="/import"
          element={
            <ProtectedRoute>
              <Import />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <AdminRoute>
              <Admin />
            </AdminRoute>
          }
        />
      </Routes>
      {!isLandingPage && !isLoginPage && !isDemoPage && <JobsBottomBar />}
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
