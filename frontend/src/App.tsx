import './index.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ActiveJobsProvider } from './contexts/ActiveJobsContext'
import { Navbar } from './components/Navbar'
import { Dashboard } from './pages/Dashboard'
import { Settings } from './pages/Settings'
import { Analytics } from './pages/Analytics'
import { DeckBuilder } from './pages/DeckBuilder'

function App() {
  return (
    <BrowserRouter>
      <ActiveJobsProvider>
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/decks" element={<DeckBuilder />} />
        </Routes>
      </ActiveJobsProvider>
    </BrowserRouter>
  )
}

export default App
