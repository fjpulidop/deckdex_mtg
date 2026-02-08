import './index.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ActiveJobsProvider } from './contexts/ActiveJobsContext'
import { Dashboard } from './pages/Dashboard'
import { Settings } from './pages/Settings'

function App() {
  return (
    <BrowserRouter>
      <ActiveJobsProvider>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </ActiveJobsProvider>
    </BrowserRouter>
  )
}

export default App
