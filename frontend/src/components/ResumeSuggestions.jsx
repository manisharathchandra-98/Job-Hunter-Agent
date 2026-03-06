import { useState } from "react";
import "./ResumeSuggestions.css";

/* ── small helpers ─────────────────────────────────────────────────────── */
function Badge({ label, variant = "neutral" }) {
  return <span className={`rs-badge rs-badge--${variant}`}>{label}</span>;
}

function impactVariant(v = "") {
  const s = v.toLowerCase();
  if (s === "high")   return "high";
  if (s === "medium") return "medium";
  return "low";
}

/* ── ScoreProjection ───────────────────────────────────────────────────── */
function ScoreProjection({ data, matchScore }) {
  if (!data) return null;
  // Use the real pipeline match_score as current if Resume Coach received 0
  const rawCurrent = data.current_score ?? 0;
  const current_score = (rawCurrent === 0 && matchScore > 0) ? matchScore : rawCurrent;
  const { projected_score = 0, confidence } = data;
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
      {confidence && (
        <div className="rs-score-projection__confidence">
          Confidence: <Badge label={confidence} variant={impactVariant(confidence)} />
        </div>
      )}
    </div>
  );
}

/* ── PriorityChanges ───────────────────────────────────────────────────── */
// Resume Coach returns: [{rank, change, impact, effort}]
function PriorityChanges({ changes }) {
  if (!changes?.length) return null;
  const sorted = [...changes].sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99));
  return (
    <div className="rs-section">
      <h4 className="rs-section__title">🎯 Priority Changes</h4>
      <div className="rs-changes">
        {sorted.map((c, i) => (
          <div key={i} className={`rs-change rs-change--${impactVariant(c.impact)}`}>
            <div className="rs-change__header">
              <span className="rs-change__rank">#{c.rank ?? i + 1}</span>
              {c.impact && <Badge label={`Impact: ${c.impact}`} variant={impactVariant(c.impact)} />}
              {c.effort && <Badge label={`Effort: ${c.effort}`} variant="neutral" />}
            </div>
            <p className="rs-change__issue">{c.change}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── KeywordsToAdd ─────────────────────────────────────────────────────── */
// Resume Coach returns: [{keyword, context}]
function KeywordsToAdd({ keywords }) {
  if (!keywords?.length) return null;
  return (
    <div className="rs-section">
      <h4 className="rs-section__title">🔑 Keywords to Add</h4>
      <div className="rs-keywords">
        {keywords.map((kw, i) => (
          <div key={i} className="rs-keyword">
            <span className="rs-keyword__word">{kw.keyword}</span>
            {kw.context && (
              <span className="rs-keyword__placement">→ {kw.context}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── BulletRewrites ────────────────────────────────────────────────────── */
// Resume Coach returns: [{original, improved, reason}]
function BulletRewrites({ rewrites }) {
  if (!rewrites?.length) return null;
  return (
    <div className="rs-section">
      <h4 className="rs-section__title">✏️ Bullet Point Rewrites</h4>
      <div className="rs-rewrites">
        {rewrites.map((r, i) => (
          <div key={i} className="rs-rewrite">
            <div className="rs-rewrite__diff">
              <div className="rs-rewrite__before">
                <label>Original</label>
                <p>{r.original}</p>
              </div>
              <div className="rs-rewrite__after">
                <label>Improved</label>
                <p>{r.improved}</p>
              </div>
            </div>
            {r.reason && (
              <p className="rs-change__reason">💡 {r.reason}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── NewBullets ────────────────────────────────────────────────────────── */
// Resume Coach returns: array of strings
function NewBullets({ bullets }) {
  if (!bullets?.length) return null;
  return (
    <div className="rs-section">
      <h4 className="rs-section__title">➕ New Bullets to Add</h4>
      <div className="rs-new-bullets">
        {bullets.map((b, i) => (
          <div key={i} className="rs-new-bullet">
            <p className="rs-new-bullet__text">
              • {typeof b === "string" ? b : b.bullet ?? JSON.stringify(b)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── SummaryRewrite ────────────────────────────────────────────────────── */
// Resume Coach returns: a plain string
function SummaryRewrite({ data }) {
  // Accept both a plain string and an object with a `suggested` key
  const text = typeof data === "string" ? data : data?.suggested;
  if (!text) return null;
  return (
    <div className="rs-section">
      <h4 className="rs-section__title">📄 Professional Summary Rewrite</h4>
      <div className="rs-summary">
        <div className="rs-summary__suggested">
          <label>Suggested</label>
          <p>{text}</p>
        </div>
      </div>
    </div>
  );
}

/* ── SkillsSectionRewrite ──────────────────────────────────────────────── */
// Resume Coach returns: a plain string (multi-line)
function SkillsSectionRewrite({ data }) {
  if (!data) return null;
  if (typeof data === "string") {
    // Split on newlines and render each line so text wraps naturally
    const lines = data.split("\n").filter(l => l.trim() !== "");
    return (
      <div className="rs-section">
        <h4 className="rs-section__title">🛠️ Skills Section Rewrite</h4>
        <div className="rs-summary">
          <div className="rs-summary__suggested">
            <label>Suggested</label>
            <div className="rs-skills-lines">
              {lines.map((line, i) => (
                <p key={i} className="rs-skills-line">{line}</p>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }
  // object form { add, remove, reorder_advice }
  return (
    <div className="rs-section">
      <h4 className="rs-section__title">🛠️ Skills Section Update</h4>
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

/* ── Main export ───────────────────────────────────────────────────────── */
export default function ResumeSuggestions({ suggestions, matchScore = 0 }) {
  const [open, setOpen] = useState(true);

  if (!suggestions || suggestions.error || Object.keys(suggestions).length === 0) {
    return null;
  }

  // The Resume Coach returns PascalCase keys:
  // ScoreProjection, PriorityChanges, KeywordsToAdd, BulletRewrites,
  // NewBullets, SummaryRewrite, SkillsSectionRewrite, OverallStrategy
  const {
    ScoreProjection:      scoreProjection,
    PriorityChanges:      priorityChanges,
    KeywordsToAdd:        keywordsToAdd,
    BulletRewrites:       bulletRewrites,
    NewBullets:           newBullets,
    SummaryRewrite:       summaryRewrite,
    SkillsSectionRewrite: skillsSectionRewrite,
    OverallStrategy:      overallStrategy,
  } = suggestions;

  return (
    <div className="rs-wrapper">
      <div className="rs-header" onClick={() => setOpen(o => !o)} style={{ cursor: "pointer" }}>
        <div>
          <h3 className="rs-header__title">📝 Resume Improvement Suggestions</h3>
          <p className="rs-header__subtitle">
            Targeted changes to increase your match score for this role
          </p>
        </div>
        <span className="rs-header__toggle">{open ? "▲" : "▼"}</span>
      </div>

      {open && (
        <>
          <ScoreProjection      data={scoreProjection} matchScore={matchScore} />
          <PriorityChanges      changes={priorityChanges} />
          <KeywordsToAdd        keywords={keywordsToAdd} />
          <BulletRewrites       rewrites={bulletRewrites} />
          <NewBullets           bullets={newBullets} />
          <SummaryRewrite       data={summaryRewrite} />
          <SkillsSectionRewrite data={skillsSectionRewrite} />

          {overallStrategy && (
            <div className="rs-strategy">
              <h4 className="rs-strategy__title">🎯 Overall Strategy</h4>
              <p className="rs-strategy__text">{overallStrategy}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
