import { useState } from 'react'
import SubmitForm   from './components/SubmitForm.jsx'
import MatchResults from './components/MatchResults.jsx'
import './App.css'
import ErrorBoundary from './components/ErrorBoundary.jsx'

const NAV = [
  { id: 'analyze', icon: '✦', label: 'Analyze Resume' },
  { id: 'results', icon: '◈', label: 'Match Results'  },
]

export default function App() {
  const [activeTab,     setActiveTab]     = useState('analyze')
  const [completedMatch,setCompletedMatch] = useState(null)

  function handleMatchComplete(data) {
    setCompletedMatch(data)
    setActiveTab('results')
  }

  return (
    <div className="app-shell">
      {/* ── Sidebar ─────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">🎯</span>
          <div>
            <div className="brand-name">Job Fit Analyzer</div>
            <div className="brand-sub">AI-Powered Matching</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-label">Navigation</div>
          {NAV.map(n => (
            <button
              key={n.id}
              className={`nav-item ${activeTab === n.id ? 'active' : ''}`}
              onClick={() => setActiveTab(n.id)}
            >
              <span className="nav-icon">{n.icon}</span>
              <span>{n.label}</span>
              {n.id === 'results' && completedMatch && (
                <span className="nav-dot" />
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="powered-by">Powered by</div>
          <div className="powered-by-stack">
            <span>Claude 3 Haiku</span>
            <span>AWS Bedrock</span>
            <span>Step Functions</span>
          </div>
        </div>
      </aside>

      {/* ── Main ────────────────────────────────────── */}
      <div className="main-wrapper">
        <header className="topbar">
          <div className="topbar-left">
            <h1 className="page-title">
              {activeTab === 'analyze' ? 'Resume Analysis' : 'Match Results'}
            </h1>
            <p className="page-sub">
              {activeTab === 'analyze'
                ? 'Submit a resume and job description to start the AI analysis pipeline'
                : 'View scores, skill gaps, and salary insights from completed analyses'}
            </p>
          </div>
          <div className="topbar-right">
            <div className="status-chip">
              <span className="status-dot" />
              Pipeline Active
            </div>
          </div>
        </header>

        <main className="main-content">
          <ErrorBoundary>
            {activeTab === 'analyze' ? (
              <SubmitForm onMatchComplete={handleMatchComplete} />
            ) : (
              <MatchResults initialMatch={completedMatch} />
            )}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}