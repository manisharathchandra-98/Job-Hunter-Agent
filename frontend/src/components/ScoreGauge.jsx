import './ScoreGauge.css'

function scoreColor(s) {
  if (s >= 75) return '#10b981'
  if (s >= 50) return '#f59e0b'
  return '#ef4444'
}

function scoreLabel(s) {
  if (s >= 80) return 'Strong Fit'
  if (s >= 65) return 'Good Fit'
  if (s >= 50) return 'Moderate Fit'
  if (s >= 35) return 'Weak Fit'
  return 'Poor Fit'
}

function recBadgeClass(rec) {
  if (!rec) return 'badge-gray'
  const r = rec.toLowerCase()
  if (r.includes('strong') || r.includes('good')) return 'badge-green'
  if (r.includes('moderate')) return 'badge-yellow'
  return 'badge-red'
}

function polarToCartesian(cx, cy, r, deg) {
  const rad = ((deg - 90) * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

function describeArc(cx, cy, r, startDeg, endDeg) {
  const s = polarToCartesian(cx, cy, r, startDeg)
  const e = polarToCartesian(cx, cy, r, endDeg)
  return `M ${s.x} ${s.y} A ${r} ${r} 0 1 1 ${e.x} ${e.y}`
}

function humanize(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export default function ScoreGauge({ matchResult }) {
  if (!matchResult) return null
  const score     = matchResult.match_score ?? 0
  const rec       = matchResult.recommendation ?? ''
  const effort    = matchResult.effort_to_match ?? ''
  const breakdown = matchResult.score_breakdown ?? {}
  const color     = scoreColor(score)
  const circumference = Math.PI * 72
  const progress      = (score / 100) * circumference

  return (
    <div className="score-gauge card fade-in">
      <p className="section-title">Overall Match Score</p>

      <div className="gauge-layout">
        {/* Score block */}
        <div className="gauge-score-block">
          <span className="gauge-number">{score}</span>
          <span className="gauge-max">/100</span>
          <span className="gauge-label">{scoreLabel(score)}</span>
        </div>

        {/* Details */}
        <div className="gauge-details">
          <div className="detail-row">
            <span className="detail-key">Recommendation</span>
            <span className={`badge ${recBadgeClass(rec)}`}>{rec}</span>
          </div>
          <div className="detail-row">
            <span className="detail-key">Effort to match</span>
            <span className="detail-val">{effort || '—'}</span>
          </div>

          {Object.keys(breakdown).length > 0 && (
            <div className="breakdown-list">
              {Object.entries(breakdown).map(([key, val]) => {
                if (key === 'overall') return null
                const pct = typeof val === 'number' ? val : 0
                return (
                  <div key={key} className="breakdown-item">
                    <div className="breakdown-label">
                      <span>{humanize(key)}</span>
                      <span>{pct}%</span>
                    </div>
                    <div className="breakdown-track">
                      <div className="breakdown-fill"
                        style={{ width: `${pct}%`, background: scoreColor(pct) }} />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {matchResult.explanation && (
        <p className="gauge-explanation">{matchResult.explanation}</p>
      )}
    </div>
  )
}