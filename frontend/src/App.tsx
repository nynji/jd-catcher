import { BrowserRouter, Route, Routes } from 'react-router-dom'
import MatchAnalysisPage from './pages/MatchAnalysisPage'
import MatchPage from './pages/MatchPage'
import PostingDetailPage from './pages/PostingDetailPage'
import PostingListPage from './pages/PostingListPage'
import ResumePage from './pages/ResumePage'
import './app-shell.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<PostingListPage />} />
        <Route path="/postings/:postingId" element={<PostingDetailPage />} />
        <Route path="/resume" element={<ResumePage />} />
        <Route path="/match/:resumeId" element={<MatchPage />} />
        <Route path="/analysis/:resumeId/:roleId" element={<MatchAnalysisPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
