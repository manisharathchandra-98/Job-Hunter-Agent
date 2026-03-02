import './GapsPanel.css'

function priorityClass(p) {
  if (!p) return 'priority-medium'
  const v = p.toLowerCase()
  if (v === 'high' || v === 'critical') return 'priority-high'
  if (v === 'low'  || v === 'minor')   return 'priority-low'
  return 'priority-medium'
}

function priorityIcon(p) {
  if (!p) return '•'
  const v = p.toLowerCase()
  if (v === 'high' || v === 'critical') return '🔴'
  if (v === 'low'  || v === 'minor')   return '🟢'
  return '🟡'
}

function severityClass(sev) {
  if (!sev) return 'sev-medium'
  const s = sev.toLowerCase()
  if (s.includes('high') || s.includes('critical')) return 'sev-high'
  if (s.includes('low')  || s.includes('minor'))    return 'sev-low'
  return 'sev-medium'
}

export default function GapsPanel({ gapData }) {
  if (!gapData) return null
  const skillGaps      = gapData.skill_gaps      ?? []
  const experienceGaps = gapData.experience_gaps ?? []
  const learningPath   = gapData.learning_path   ?? []
  const severity       = gapData.overall_gap_severity ?? null
  const summary        = gapData.gap_summary ?? gapData.summary ?? null

  if (!skillGaps.length && !experienceGaps.length && !learningPath.length) return null

  return (
    <div className="gaps-panel card fade-in">
      <div className="gaps-header">
        <h3 className="section-title" style={{ marginBottom: 0 }}>Gap Analysis</h3>
        {severity && (
          <span className={`severity-badge ${severityClass(severity)}`}>
            {severity.replace(/_/g,' ')} severity
          </span>
        )}
      </div>
      {summary && <p className="gaps-summary">{summary}</p>}

      <div className="gaps-body">
        {skillGaps.length > 0 && (
          <section className="gap-section">
            <h4 className="gap-section-title">Skill Gaps</h4>
            <div className="gap-list">
              {skillGaps.map((gap, i) => {
                const name     = gap.skill_name ?? gap.skill ?? gap.name ?? gap
                const priority = gap.priority ?? gap.importance ?? null
                const time     = gap.time_to_acquire ?? null
                const note     = gap.note ?? gap.description ?? null
                return (
                  <div key={i} className={`gap-item ${priorityClass(priority)}`}>
                    <div className="gap-row">
                      <span className="gap-icon">{priorityIcon(priority)}</span>
                      <span className="gap-name">{name}</span>
                      {priority && <span className="gap-priority">{priority}</span>}
                      {time     && <span className="gap-time">~{time}</span>}
                    </div>
                    {note && <p className="gap-note">{note}</p>}
                  </div>
                )
              })}
            </div>
          </section>
        )}

        {experienceGaps.length > 0 && (
          <section className="gap-section">
            <h4 className="gap-section-title">Experience Gaps</h4>
            <div className="gap-list">
              {experienceGaps.map((gap, i) => {
                const area     = gap.area ?? gap.domain ?? gap
                const required = gap.required ?? null
                const note     = gap.note ?? gap.description ?? null
                return (
                  <div key={i} className="gap-item exp-gap">
                    <div className="gap-row">
                      <span className="gap-icon">📋</span>
                      <span className="gap-name">{area}</span>
                      {required && <span className="gap-time">Needs: {required}</span>}
                    </div>
                    {note && <p className="gap-note">{note}</p>}
                  </div>
                )
              })}
            </div>
          </section>
        )}

        {learningPath.length > 0 && (
          <section className="gap-section">
            <h4 className="gap-section-title">Recommended Learning Path</h4>
            <ol className="learning-list">
              {learningPath.map((step, i) => {
                const title    = step.skill ?? step.topic ?? step.title ?? step
                const resource = step.resource ?? step.course ?? step.platform ?? null
                const duration = step.duration ?? step.time ?? null
                return (
                  <li key={i} className="learning-item">
                    <div className="learning-title">{title}</div>
                    {(resource || duration) && (
                      <div className="learning-meta">
                        {resource && <span>{resource}</span>}
                        {duration && <span>{duration}</span>}
                      </div>
                    )}
                  </li>
                )
              })}
            </ol>
          </section>
        )}
      </div>
    </div>
  )
}