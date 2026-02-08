import './index.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ActiveJobsProvider } from './contexts/ActiveJobsContext'
import { Dashboard } from './pages/Dashboard'
import { Settings } from './pages/Settings'
import { Analytics } from './pages/Analytics'

function App() {
  return (
    <BrowserRouter>
      <ActiveJobsProvider>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </ActiveJobsProvider>
    </BrowserRouter>
  )
}

export default App
