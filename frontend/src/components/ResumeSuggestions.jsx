import "./ResumeSuggestions.css";

const PRIORITY_ORDER = { HIGH: 0, MEDIUM: 1, LOW: 2 };

function PriorityBadge({ priority }) {
  return (
    <span className={`rs-badge rs-badge--${priority.toLowerCase()}`}>
      {priority}
    </span>
  );
}

function ActionBadge({ action }) {
  return (
    <span className={`rs-action rs-action--${action.toLowerCase()}`}>
      {action}
    </span>
  );
}

function ScoreProjection({ data }) {
  if (!data) return null;
  const { current_score, projected_score, improvement_breakdown } = data;
  const gain = projected_score - current_score;

  return (
    <div className="rs-score-projection">
      <div className="rs-score-projection__scores">
        <div className="rs-score-projection__item">
          <span className="rs-score-projection__label">Current Score</span>
          <span className="rs-score-projection__value rs-score-projection__value--current">
            {current_score}
          </span>
        </div>
        <div className="rs-score-projection__arrow">→</div>
        <div className="rs-score-projection__item">
          <span className="rs-score-projection__label">Projected Score</span>
          <span className="rs-score-projection__value rs-score-projection__value--projected">
            {projected_score}
          </span>
        </div>
        {gain > 0 && (
          <div className="rs-score-projection__gain">+{gain} pts</div>
        )}
      </div>
      {improvement_breakdown && (
        <div className="rs-score-projection__breakdown">
          {Object.entries(improvement_breakdown).map(([key, val]) => (
            <span key={key} className="rs-score-projection__pill">
              {key.replace(/_/g, " ")}: <strong>{val}</strong>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function PriorityChanges({ changes }) {
  if (!changes?.length) return null;

  const sorted = [...changes].sort(
    (a, b) => (PRIORITY_ORDER[a.priority] ?? 99) - (PRIORITY_ORDER[b.priority] ?? 99)
  );

  return (
    <div className="rs-section">
      <h4 className="rs-section__title">Priority Changes</h4>
      <div className="rs-changes">
        {sorted.map((c, i) => (
          <div key={i} className={`rs-change rs-change--${c.priority.toLowerCase()}`}>
            <div className="rs-change__header">
              <PriorityBadge priority={c.priority} />
              <ActionBadge action={c.action} />
              <span className="rs-change__section">{c.section}</span>
            </div>
            <p className="rs-change__issue">{c.issue}</p>

            {c.current_text ? (
              <div className="rs-change__diff">
                <div className="rs-change__before">
                  <label>Before</label>
                  <p>{c.current_text}</p>
                </div>
                <div className="rs-change__after">
                  <label>After</label>
                  <p>{c.suggested_text}</p>
                </div>
              </div>
            ) : (
              <div className="rs-change__add">
                <label>Add this</label>
                <p>{c.suggested_text}</p>
              </div>
            )}

            <p className="rs-change__reason">💡 {c.reason}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function KeywordsToAdd({ keywords }) {
  if (!keywords?.length) return null;
  return (
    <div className="rs-section">
      <h4 className="rs-section__title">Keywords to Add</h4>
      <div className="rs-keywords">
        {keywords.map((kw, i) => (
          <div
            key={i}
            className={`rs-keyword rs-keyword--${kw.frequency_in_jd}`}
            title={kw.example_usage}
          >
            <span className="rs-keyword__word">{kw.keyword}</span>
            <span className="rs-keyword__placement">{kw.suggested_placement}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function BulletRewrites({ rewrites }) {
  if (!rewrites?.length) return null;
  return (
    <div className="rs-section">
      <h4 className="rs-section__title">Bullet Point Rewrites</h4>
      <div className="rs-rewrites">
        {rewrites.map((r, i) => (
          <div key={i} className="rs-rewrite">
            <div className="rs-rewrite__type">{r.improvement_type}</div>
            <div className="rs-rewrite__diff">
              <div className="rs-rewrite__before">
                <label>Original</label>
                <p>{r.original}</p>
              </div>
              <div className="rs-rewrite__after">
                <label>Rewritten</label>
                <p>{r.rewritten}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function NewBullets({ bullets }) {
  if (!bullets?.length) return null;
  return (
    <div className="rs-section">
      <h4 className="rs-section__title">New Bullets to Add</h4>
      <div className="rs-new-bullets">
        {bullets.map((b, i) => (
          <div key={i} className="rs-new-bullet">
            <div className="rs-new-bullet__meta">
              <span className="rs-new-bullet__target">📌 {b.target_role_or_project}</span>
              <span className="rs-new-bullet__gap">Addresses: {b.gap_addressed}</span>
            </div>
            <p className="rs-new-bullet__text">• {b.bullet}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function SummaryRewrite({ data }) {
  if (!data?.suggested) return null;
  return (
    <div className="rs-section">
      <h4 className="rs-section__title">Professional Summary Rewrite</h4>
      <div className="rs-summary">
        {data.original && (
          <div className="rs-summary__original">
            <label>Current</label>
            <p>{data.original}</p>
          </div>
        )}
        <div className="rs-summary__suggested">
          <label>Suggested</label>
          <p>{data.suggested}</p>
        </div>
        {data.ats_keywords_included?.length > 0 && (
          <div className="rs-summary__keywords">
            <span>ATS keywords included: </span>
            {data.ats_keywords_included.map((kw, i) => (
              <span key={i} className="rs-summary__kw-chip">{kw}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SkillsSectionRewrite({ data }) {
  if (!data) return null;
  return (
    <div className="rs-section">
      <h4 className="rs-section__title">Skills Section Update</h4>
      <div className="rs-skills-rewrite">
        {data.add?.length > 0 && (
          <div className="rs-skills-rewrite__row">
            <span className="rs-skills-rewrite__label rs-skills-rewrite__label--add">Add</span>
            <div className="rs-skills-rewrite__chips">
              {data.add.map((s, i) => (
                <span key={i} className="rs-skills-rewrite__chip rs-skills-rewrite__chip--add">{s}</span>
              ))}
            </div>
          </div>
        )}
        {data.remove?.length > 0 && (
          <div className="rs-skills-rewrite__row">
            <span className="rs-skills-rewrite__label rs-skills-rewrite__label--remove">Remove</span>
            <div className="rs-skills-rewrite__chips">
              {data.remove.map((s, i) => (
                <span key={i} className="rs-skills-rewrite__chip rs-skills-rewrite__chip--remove">{s}</span>
              ))}
            </div>
          </div>
        )}
        {data.reorder_advice && (
          <p className="rs-skills-rewrite__advice">📋 {data.reorder_advice}</p>
        )}
      </div>
    </div>
  );
}

export default function ResumeSuggestions({ suggestions }) {
  // Don't render anything if no suggestions or if agent returned an error
  if (!suggestions || suggestions.error || Object.keys(suggestions).length === 0) {
    return null;
  }

  return (
    <div className="rs-wrapper">
      <div className="rs-header">
        <h3 className="rs-header__title">📝 Resume Improvement Suggestions</h3>
        <p className="rs-header__subtitle">
          Targeted changes to increase your match score for this role
        </p>
      </div>

      <ScoreProjection data={suggestions.estimated_score_after_changes} />
      <PriorityChanges changes={suggestions.priority_changes} />
      <KeywordsToAdd keywords={suggestions.keywords_to_add} />
      <BulletRewrites rewrites={suggestions.bullet_rewrites} />
      <NewBullets bullets={suggestions.new_bullets_to_add} />
      <SummaryRewrite data={suggestions.summary_rewrite} />
      <SkillsSectionRewrite data={suggestions.skills_section_rewrite} />

      {suggestions.overall_strategy && (
        <div className="rs-strategy">
          <h4 className="rs-strategy__title">🎯 Overall Strategy</h4>
          <p className="rs-strategy__text">{suggestions.overall_strategy}</p>
        </div>
      )}
    </div>
  );
}