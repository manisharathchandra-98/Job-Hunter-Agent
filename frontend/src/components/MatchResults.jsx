import { useState, useEffect } from 'react'
import { getMatch, getCandidateMatches } from '../api.js'
import ScoreGauge      from './ScoreGauge.jsx'
import SkillsBreakdown from './SkillsBreakdown.jsx'
import GapsPanel       from './GapsPanel.jsx'
import SalaryInsights  from './SalaryInsights.jsx'
import './MatchResults.css'
import ResumeSuggestions from "./ResumeSuggestions";

export default function MatchResults({ initialMatch }) {
  const [view,       setView]       = useState('result')
  const [matchData,  setMatchData]  = useState(initialMatch)
  const [loading,    setLoading]    = useState(false)
  const [error,      setError]      = useState(null)
  const [lookupId,   setLookupId]   = useState('')
  const [candidateId,setCandidateId]= useState('')
  const [historyData,setHistoryData]= useState(null)
  const [histLoading,setHistLoading]= useState(false)

  useEffect(() => {
    if (initialMatch) { setMatchData(initialMatch); setView('result'); setError(null) }
  }, [initialMatch])

  async function handleLookup(e) {
    e.preventDefault()
    if (!lookupId.trim()) return
    setLoading(true); setError(null)
    try {
      const { data, status } = await getMatch(lookupId.trim())
      if (status === 200)      { setMatchData(data); setView('result') }
      else if (status === 202) setError('Still processing - check back in a moment.')
      else                     setError(data?.error || 'Match not found.')
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  async function handleHistoryLookup(e) {
    e.preventDefault()
    if (!candidateId.trim()) return
    setHistLoading(true); setError(null)
    try {
      const data = await getCandidateMatches(candidateId.trim())
      setHistoryData(data)
    } catch (err) { setError(err.message) }
    finally { setHistLoading(false) }
  }

  return (
    <div className="match-results-page">
      <div className="sub-nav">
        {['result','lookup','history'].map(v => (
          <button key={v} className={`sub-btn ${view===v?'active':''}`} onClick={() => setView(v)}>
            {v === 'result' ? 'Result' : v === 'lookup' ? 'Look up by ID' : 'Candidate history'}
          </button>
        ))}
      </div>

      {view === 'result' && (
        matchData ? <MatchDetail match={matchData} /> : <EmptyState />
      )}

      {view === 'lookup' && (
        <div className="lookup-card card fade-in">
          <h3 className="lookup-title">Look up a match by ID</h3>
          <form className="lookup-form" onSubmit={handleLookup}>
            <input placeholder="Enter match ID (UUID)" value={lookupId} onChange={e => setLookupId(e.target.value)}/>
            <button type="submit" className="btn-primary" disabled={loading || !lookupId.trim()}>
              {loading ? <span className="spinner"/> : 'Fetch'}
            </button>
          </form>
          {error && <p className="lookup-error">{error}</p>}
        </div>
      )}

      {view === 'history' && (
        <div className="fade-in">
          <div className="lookup-card card">
            <h3 className="lookup-title">Candidate match history</h3>
            <form className="lookup-form" onSubmit={handleHistoryLookup}>
              <input placeholder="Enter candidate ID (UUID)" value={candidateId} onChange={e => setCandidateId(e.target.value)}/>
              <button type="submit" className="btn-primary" disabled={histLoading || !candidateId.trim()}>
                {histLoading ? <span className="spinner"/> : 'Load history'}
              </button>
            </form>
            {error && <p className="lookup-error">{error}</p>}
          </div>
          {historyData && <HistoryList history={historyData} onSelect={m => { setMatchData(m); setView('result') }}/>}
        </div>
      )}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="empty-state card fade-in">
      <div className="empty-icon">📄</div>
      <h3>No result yet</h3>
      <p>Go to <strong>Analyze Resume</strong> and submit a resume + job description. Results appear here automatically.</p>
      <p style={{fontSize:'0.875rem',color:'var(--text-muted)'}}>Or use <strong>Look up by ID</strong> if you have a match ID.</p>
    </div>
  )
}

function MatchDetail({ match }) {
  // Normalize aggregator's flat structure into what sub-components expect Ã¢â€â‚¬Ã¢â€â‚¬

  // ScoreGauge: needs match_score, score_breakdown, recommendation etc.
  const matchResult = match.match_result ?? {
    match_score:     match.match_score,
    score_breakdown: match.score_breakdown,
    recommendation:  match.recommendation,
    effort_to_match: match.effort_to_match,
    explanation:     match.explanation,
  }

  // SkillsBreakdown: needs matched_skills, missing_skills
  const skillsData = match.skills_analysis ?? null

  // SalaryInsights: needs market_value.salary_low/median/high
  // Aggregator stores as salary_insights.candidate_market_value instead
  const rawSalary  = match.market_analysis ?? match.salary_insights ?? null
  const salaryData = rawSalary ? {
    ...rawSalary,
    job_title:       match.job_title_detected ?? rawSalary.job_title,
    market_position: rawSalary.market_position,
    market_demand:   rawSalary.market_demand,
    salary_note:     rawSalary.market_insight ?? null,
    // Map flat value Ã¢â€ â€™ range that SalaryInsights renders as a bar
    market_value: rawSalary.market_value ?? (rawSalary.candidate_market_value ? {
      salary_low:    Math.round(rawSalary.candidate_market_value * 0.85),
      salary_median: rawSalary.candidate_market_value,
      salary_high:   rawSalary.earning_potential_6months
                       ?? Math.round(rawSalary.candidate_market_value * 1.15),
    } : null),
  } : null

  // GapsPanel: needs skill_gaps[], gap_summary, overall_gap_severity
  // Aggregator stores as gaps.critical[], gaps.important[], gaps.nice_to_have[]
  const rawGapAnalysis = match.gap_analysis ?? null
  const gapData = rawGapAnalysis ?? (match.gaps ? {
    skill_gaps: [
      ...(match.gaps.critical     ?? []).map(g => ({
        skill_name: g.skill, priority: 'high',
        time_to_acquire: g.learning_time_weeks ? `${g.learning_time_weeks} weeks` : null,
        note: g.resource ?? null,
      })),
      ...(match.gaps.important    ?? []).map(g => ({
        skill_name: g.skill, priority: 'medium',
        time_to_acquire: g.learning_time_weeks ? `${g.learning_time_weeks} weeks` : null,
        note: g.resource ?? null,
      })),
      ...(match.gaps.nice_to_have ?? []).map(g => ({
        skill_name: g.skill, priority: 'low',
        time_to_acquire: g.learning_time_weeks ? `${g.learning_time_weeks} weeks` : null,
        note: g.resource ?? null,
      })),
    ],
    gap_summary: match.overall_recommendation ?? null,
    overall_gap_severity:
      (match.gaps.critical?.length     > 0) ? 'high'   :
      (match.gaps.important?.length    > 0) ? 'medium' : 'low',
  } : null)

  // Learning path from learning_plan.timeline
  const learningPath = match.learning_plan?.timeline ?? []
  if (gapData && learningPath.length > 0) {
    gapData.learning_path = learningPath.map(t => ({
      skill:    t.focus,
      resource: t.action,
    }))
  }

  const parsedJob  = match.parsed_job   ?? { job_title: match.job_title_detected }
  const parsedCand = match.parsed_candidate ?? null

  return (
    <div className="match-detail fade-in">
      {/* Header */}
      <div className="match-detail-header">
        <div>
          <h2 className="match-detail-title">
            {parsedJob?.job_title ?? match.job_title_detected ?? 'Match Analysis'}
          </h2>
          {parsedCand?.name && (
            <p className="match-detail-sub">Candidate: {parsedCand.name}</p>
          )}
        </div>
        <div className="match-meta">
          {match.match_id && (
            <div className="meta-item">
              <span className="meta-label">Match ID</span>
              <code className="meta-code">{match.match_id.slice(0, 8)}...</code>
            </div>
          )}
          {match.created_at && (
            <div className="meta-item">
              <span className="meta-label">Analyzed</span>
              <span className="meta-val">
                {new Date(match.created_at).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Sections */}
      <div className="detail-sections">
        <ScoreGauge      matchResult={matchResult} />
        <SkillsBreakdown skillsData={skillsData}   parsedJob={parsedJob} />
        <GapsPanel       gapData={gapData} />
        <SalaryInsights  salaryData={salaryData}   parsedJob={parsedJob} />
      </div>

      <ResumeSuggestions suggestions={match.resume_suggestions} matchScore={match.match_score}/>
      <RawJson data={match} />
    </div>
  )
}

function HistoryList({ history, onSelect }) {
  const matches = history.matches ?? []
  if (!matches.length) return <div className="empty-state card fade-in" style={{marginTop:'1rem'}}><p>No matches found.</p></div>
  return (
    <div style={{marginTop:'1rem',display:'flex',flexDirection:'column',gap:'0.625rem'}} className="fade-in">
      <p style={{fontSize:'0.875rem',color:'var(--text-muted)',fontWeight:500}}>{matches.length} match{matches.length!==1?'es':''} found</p>
      {matches.map(m => {
        const score = m.match_result?.match_score ?? 'Ã¢â‚¬â€'
        const rec   = m.match_result?.recommendation ?? ''
        const title = m.parsed_job?.job_title ?? 'Unknown role'
        const date  = m.created_at ? new Date(m.created_at).toLocaleDateString() : ''
        return (
          <div key={m.match_id} className="history-item card" onClick={() => onSelect(m)}>
            <div className="history-row">
              <div>
                <div className="history-title">{title}</div>
                {date && <div className="history-date">{date}</div>}
              </div>
              <div className="history-score-wrap">
                {rec && <span className={`badge ${rec.toLowerCase().includes('strong')||rec.toLowerCase().includes('good')?'badge-green':rec.toLowerCase().includes('mod')?'badge-yellow':'badge-red'}`}>{rec}</span>}
                <span className="history-score">{score}</span>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function RawJson({ data }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="raw-json-wrap card">
      <button className="raw-json-toggle" onClick={() => setOpen(o => !o)}>
      {open ? '▲' : '▼'} Raw JSON response
      </button>
      {open && <pre className="raw-json">{JSON.stringify(data, null, 2)}</pre>}
    </div>
  )
}
