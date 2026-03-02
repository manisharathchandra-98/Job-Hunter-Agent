// frontend/src/components/SubmitForm.jsx
import { useState, useRef } from 'react';
import { postMatch, pollMatch } from '../api';
import './SubmitForm.css';

const STEPS = [
  { label: 'Submitting request…',       pct: 10 },
  { label: 'Parsing resume…',           pct: 28 },
  { label: 'Extracting skills…',        pct: 45 },
  { label: 'Analysing salary data…',    pct: 62 },
  { label: 'Scoring match difficulty…', pct: 76 },
  { label: 'Identifying skill gaps…',   pct: 88 },
  { label: 'Finalising results…',       pct: 95 },
];

const EXAMPLE_RESUME = `John Smith
Senior Software Engineer | john.smith@email.com | LinkedIn: /in/johnsmith

SUMMARY
Results-driven engineer with 8 years building distributed systems at scale.

EXPERIENCE
Senior Software Engineer — Stripe (2020–Present)
- Led migration of payment processing service to microservices (Python, Kubernetes)
- Reduced API latency by 40% through caching layer redesign (Redis)
- Mentored team of 4 junior engineers

Software Engineer — Airbnb (2017–2020)
- Built real-time pricing engine handling 50K req/sec (Go, Kafka)
- Implemented A/B testing framework used across 12 product teams

SKILLS
Python, Go, JavaScript, React, AWS, Kubernetes, Docker, PostgreSQL, Redis, Kafka

EDUCATION
B.S. Computer Science — UC Berkeley, 2017`;

const EXAMPLE_JD = `Senior Software Engineer — Payments Platform

We are looking for an experienced engineer to join our Payments team.

Requirements:
- 5+ years of software engineering experience
- Strong proficiency in Python or Go
- Experience with distributed systems and microservices
- Familiarity with AWS services (Lambda, SQS, DynamoDB)
- Experience with Kubernetes or container orchestration
- Strong communication skills and ability to mentor junior engineers

Nice to have:
- Experience in fintech or payments
- Knowledge of Kafka or event-driven architecture
- React or frontend experience

Compensation: $160,000 – $200,000 + equity`;

// Validation rules
const VALIDATIONS = {
  resume: [
    { test: v => v.trim().length > 0,   msg: 'Resume is required.' },
    { test: v => v.trim().length >= 100, msg: 'Resume seems too short — please paste the full text (at least 100 characters).' },
    { test: v => v.trim().length <= 20000, msg: 'Resume is too long — please trim to under 20,000 characters.' },
  ],
  jd: [
    { test: v => v.trim().length > 0,   msg: 'Job description is required.' },
    { test: v => v.trim().length >= 50,  msg: 'Job description seems too short (at least 50 characters).' },
    { test: v => v.trim().length <= 5000, msg: 'Job description is too long — please trim to under 5,000 characters.' },
  ],
};

function validate(field, value) {
  for (const rule of VALIDATIONS[field]) {
    if (!rule.test(value)) return rule.msg;
  }
  return null;
}

export default function SubmitForm({ onMatchComplete }) {
  const [resume, setResume]         = useState('');
  const [jd, setJd]                 = useState('');
  const [errors, setErrors]         = useState({ resume: null, jd: null });
  const [touched, setTouched]       = useState({ resume: false, jd: false });
  const [loading, setLoading]       = useState(false);
  const [stepIdx, setStepIdx]       = useState(0);
  const [submitError, setSubmitError] = useState(null);
  const cancelRef = useRef(null);

  const handleBlur = (field) => {
    setTouched(t => ({ ...t, [field]: true }));
    setErrors(e => ({
      ...e,
      [field]: validate(field, field === 'resume' ? resume : jd),
    }));
  };

  const handleChange = (field, value) => {
    if (field === 'resume') setResume(value);
    else setJd(value);
    if (touched[field]) {
      setErrors(e => ({ ...e, [field]: validate(field, value) }));
    }
  };

  const loadExample = () => {
    setResume(EXAMPLE_RESUME);
    setJd(EXAMPLE_JD);
    setErrors({ resume: null, jd: null });
    setTouched({ resume: false, jd: false });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Force-validate both fields on submit
    const resumeErr = validate('resume', resume);
    const jdErr     = validate('jd', jd);
    setTouched({ resume: true, jd: true });
    setErrors({ resume: resumeErr, jd: jdErr });
    if (resumeErr || jdErr) return;

    setLoading(true);
    setSubmitError(null);
    setStepIdx(0);

    const stepTimer = setInterval(() => {
      setStepIdx(i => (i < STEPS.length - 1 ? i + 1 : i));
    }, 2200);

    try {
      const { match_id } = await postMatch(resume, jd);
      cancelRef.current = pollMatch(
        match_id,
        (data) => {
          clearInterval(stepTimer);
          setLoading(false);
          onMatchComplete(data);
        },
        (err) => {
          clearInterval(stepTimer);
          setLoading(false);
          setSubmitError(err || 'Analysis failed. Please try again.');
        }
      );
    } catch (err) {
      clearInterval(stepTimer);
      setLoading(false);
      setSubmitError(err.message || 'Failed to submit. Please check your connection.');
    }
  };

  const handleCancel = () => {
    if (cancelRef.current) cancelRef.current();
    setLoading(false);
    setStepIdx(0);
    setSubmitError(null);
  };

  const resumeInvalid = touched.resume && errors.resume;
  const jdInvalid     = touched.jd && errors.jd;
  const charOk = (n, max) => n <= max * 0.9 ? 'ok' : n <= max ? 'warn' : 'over';

  return (
    <div className="sf-card">
      <div className="sf-header">
        <div>
          <h2 className="sf-title">Resume Analyzer</h2>
          <p className="sf-sub">Paste your resume and a job description to get an instant AI-powered match score.</p>
        </div>
        <button className="btn-example" onClick={loadExample} disabled={loading}>
          Load example
        </button>
      </div>

      {submitError && (
        <div className="sf-alert sf-alert--error" role="alert">
          <span className="sf-alert__icon">⚠</span>
          <span>{submitError}</span>
          <button className="sf-alert__close" onClick={() => setSubmitError(null)}>✕</button>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="sf-fields">

          {/* Resume */}
          <div className={`sf-field ${resumeInvalid ? 'sf-field--error' : ''}`}>
            <div className="sf-label-row">
              <label htmlFor="resume">Resume</label>
              <span className={`sf-chars sf-chars--${charOk(resume.length, 20000)}`}>
                {resume.length.toLocaleString()} / 8,000
              </span>
            </div>
            <textarea
              id="resume"
              className={`sf-textarea ${resumeInvalid ? 'is-invalid' : ''}`}
              placeholder="Paste your full resume here…"
              value={resume}
              rows={16}
              disabled={loading}
              onChange={e => handleChange('resume', e.target.value)}
              onBlur={() => handleBlur('resume')}
              aria-describedby={resumeInvalid ? 'resume-error' : undefined}
            />
            {resumeInvalid && (
              <p id="resume-error" className="sf-field-error" role="alert">
                <span>⚠</span> {errors.resume}
              </p>
            )}
          </div>

          {/* Job Description */}
          <div className={`sf-field ${jdInvalid ? 'sf-field--error' : ''}`}>
            <div className="sf-label-row">
              <label htmlFor="jd">Job Description</label>
              <span className={`sf-chars sf-chars--${charOk(jd.length, 5000)}`}>
                {jd.length.toLocaleString()} / 5,000
              </span>
            </div>
            <textarea
              id="jd"
              className={`sf-textarea ${jdInvalid ? 'is-invalid' : ''}`}
              placeholder="Paste the full job description here…"
              value={jd}
              rows={16}
              disabled={loading}
              onChange={e => handleChange('jd', e.target.value)}
              onBlur={() => handleBlur('jd')}
              aria-describedby={jdInvalid ? 'jd-error' : undefined}
            />
            {jdInvalid && (
              <p id="jd-error" className="sf-field-error" role="alert">
                <span>⚠</span> {errors.jd}
              </p>
            )}
          </div>

        </div>

        {/* Progress / Submit */}
        {loading ? (
          <div className="sf-progress">
            <div className="sf-progress-bar">
              <div
                className="sf-progress-fill"
                style={{ width: `${STEPS[stepIdx].pct}%` }}
              />
            </div>
            <p className="sf-progress-label">{STEPS[stepIdx].label}</p>
            <button type="button" className="btn-cancel" onClick={handleCancel}>
              Cancel
            </button>
          </div>
        ) : (
          <div className="sf-actions">
            <button type="submit" className="btn-primary">
              Analyze Match →
            </button>
          </div>
        )}
      </form>
    </div>
  );
}
