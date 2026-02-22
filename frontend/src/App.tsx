import './index.css'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { ActiveJobsProvider } from './contexts/ActiveJobsContext'
import { AuthProvider } from './contexts/AuthContext'
import { Navbar } from './components/Navbar'
import { Dashboard } from './pages/Dashboard'
import { Settings } from './pages/Settings'
import { Analytics } from './pages/Analytics'
import { DeckBuilder } from './pages/DeckBuilder'
import Login from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'

function AppContent() {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';

  return (
    <>
      {!isLoginPage && <Navbar />}
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
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
