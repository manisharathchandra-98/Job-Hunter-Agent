import './SalaryInsights.css'

function fmt(val) {
  if (val == null) return '—'
  const n = typeof val === 'string' ? parseFloat(val) : val
  return isNaN(n) ? val : '$' + n.toLocaleString('en-US', { maximumFractionDigits: 0 })
}

function posBadge(pos) {
  if (!pos) return 'badge-gray'
  const p = pos.toLowerCase()
  if (p === 'lead' || p === 'principal') return 'badge-purple'
  if (p === 'senior') return 'badge-blue'
  if (p === 'mid')    return 'badge-green'
  return 'badge-yellow'
}

function demandBadge(d) {
  if (!d) return 'badge-gray'
  const v = d.toLowerCase()
  if (v.includes('very')) return 'badge-purple'
  if (v === 'high')       return 'badge-blue'
  if (v === 'medium')     return 'badge-yellow'
  return 'badge-gray'
}

export default function SalaryInsights({ salaryData, parsedJob }) {
  if (!salaryData) return null
  const market   = salaryData.market_value ?? {}
  const title    = salaryData.job_title ?? parsedJob?.job_title ?? ''
  const position = salaryData.market_position ?? null
  const demand   = salaryData.market_demand ?? null
  const conf     = salaryData.salary_confidence ?? null
  const note     = salaryData.salary_note ?? salaryData.notes ?? null

  const low    = market.salary_low    ?? market.low    ?? null
  const median = market.salary_median ?? market.median ?? null
  const high   = market.salary_high   ?? market.high   ?? null

  if (low == null && median == null && high == null) return null

  const medianPct = (low != null && high != null && high !== low)
    ? ((median - low) / (high - low)) * 100 : 50

    return (
      <div className="salary-insights card fade-in">
        <p className="section-title">Salary Insights</p>
        {title && <p className="salary-title-line">Market benchmarks for <strong>{title}</strong></p>}
  
        {/* Three number blocks */}
        {(low != null || median != null || high != null) && (
          <div className="salary-numbers">
            {low    != null && <div className="salary-num-block"><div className="salary-num-label">Low</div><div className="salary-num-value">{fmt(low)}</div></div>}
            {median != null && <div className="salary-num-block median"><div className="salary-num-label">Median</div><div className="salary-num-value">{fmt(median)}</div></div>}
            {high   != null && <div className="salary-num-block"><div className="salary-num-label">High</div><div className="salary-num-value">{fmt(high)}</div></div>}
          </div>
        )}
  
        {/* Range bar */}
        {low != null && high != null && (
          <div style={{marginBottom:'1.25rem'}}>
            <div className="range-bar">
              {median != null && <div className="range-median-marker" style={{left:`${Math.min(Math.max(medianPct,5),95)}%`}} />}
            </div>
            <div className="range-labels"><span>{fmt(low)}</span><span>{fmt(high)}</span></div>
          </div>
        )}
  
        <div className="salary-meta">
          {position && <div className="meta-chip"><span className="meta-label">Market position</span><span className={`badge ${posBadge(position)}`}>{position.replace(/_/g,' ')}</span></div>}
          {demand   && <div className="meta-chip"><span className="meta-label">Demand</span><span className={`badge ${demandBadge(demand)}`}>{demand.replace(/_/g,' ')}</span></div>}
          {conf     && <div className="meta-chip"><span className="meta-label">Confidence</span><span className="meta-val">{conf}</span></div>}
        </div>
        {note && <p className="salary-note">{note}</p>}
      </div>
    )
}