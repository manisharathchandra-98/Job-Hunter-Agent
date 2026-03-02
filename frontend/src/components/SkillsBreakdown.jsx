import './SkillsBreakdown.css'

function demandBadge(d) {
  if (!d) return 'badge-gray'
  const v = d.toLowerCase()
  if (v.includes('very_high') || v.includes('very high')) return 'badge-purple'
  if (v === 'high')   return 'badge-blue'
  if (v === 'medium') return 'badge-yellow'
  return 'badge-gray'
}

function SkillTag({ skill, variant }) {
  const name = typeof skill === 'object' ? (skill.skill_name ?? skill.name ?? '?') : skill
  return <span className={`skill-tag skill-tag-${variant}`}>{name}</span>
}

export default function SkillsBreakdown({ skillsData, parsedJob }) {
  if (!skillsData) return null
  const required  = skillsData.required_skills  ?? []
  const matched   = skillsData.matched_skills   ?? []
  const missing   = skillsData.missing_skills   ?? []
  const bonus     = skillsData.bonus_skills     ?? []
  const jobTitle  = parsedJob?.job_title ?? ''

  if (!matched.length && !missing.length && !bonus.length) return null

  return (
    <div className="skills-breakdown card fade-in">
      <h3 className="section-title">Skills Analysis</h3>
      {jobTitle && <p className="skills-subtitle">Required skills for <strong>{jobTitle}</strong></p>}

      <div className="skills-grid">
        {matched.length > 0 && (
          <div className="skill-group">
            <div className="skill-group-header matched-header">
              <span>✓ Matched Skills</span><span className="skill-count">{matched.length}</span>
            </div>
            <div className="skill-tags">{matched.map((s,i) => <SkillTag key={i} skill={s} variant="matched"/>)}</div>
          </div>
        )}
        {missing.length > 0 && (
          <div className="skill-group">
            <div className="skill-group-header missing-header">
              <span>✗ Missing Skills</span><span className="skill-count">{missing.length}</span>
            </div>
            <div className="skill-tags">{missing.map((s,i) => <SkillTag key={i} skill={s} variant="missing"/>)}</div>
          </div>
        )}
        {bonus.length > 0 && (
          <div className="skill-group">
            <div className="skill-group-header bonus-header">
              <span>★ Bonus Skills</span><span className="skill-count">{bonus.length}</span>
            </div>
            <div className="skill-tags">{bonus.map((s,i) => <SkillTag key={i} skill={s} variant="bonus"/>)}</div>
          </div>
        )}
      </div>

      {required.length > 0 && typeof required[0] === 'object' && (
        <div className="market-table-wrap">
          <h4 className="subsection-title">Market Demand by Skill</h4>
          <div className="market-table">
            {required.map((s, i) => {
              const name   = s.skill_name ?? s.name ?? s
              const demand = s.market_demand ?? null
              const level  = s.proficiency_level ?? null
              const years  = s.years_required ?? null
              return (
                <div key={i} className="market-row">
                  <span className="market-skill">{name}</span>
                  {level  && <span className="market-meta">{level}</span>}
                  {years != null && <span className="market-meta">{years}yr+</span>}
                  {demand && <span className={`badge ${demandBadge(demand)}`}>{demand.replace(/_/g,' ')}</span>}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}