// frontend/src/api.js
const BASE = 'https://frapi46611.execute-api.us-east-1.amazonaws.com/prod';

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': import.meta.env.VITE_API_KEY,
      },
      ...options,
    });
  } catch (networkErr) {
    // No response at all — DNS failure, CORS preflight blocked, offline
    throw new Error('Network error — please check your internet connection.');
  }

  let data;
  try {
    data = await res.json();
  } catch {
    throw new Error(`Server returned an unexpected response (HTTP ${res.status}).`);
  }

  if (!res.ok) {
    // Use the backend's error message if available, otherwise generic
    const msg = data?.error || `Request failed with status ${res.status}.`;
    const err = new Error(msg);
    err.code   = data?.code   || null;
    err.status = res.status;
    throw err;
  }

  return { data, status: res.status };
}

export async function postMatch(resumeText, jobDescription) {
  const { data } = await request('/match', {
    method: 'POST',
    body: JSON.stringify({
      resume_text:     resumeText,
      job_description: jobDescription,
    }),
  });
  return data;
}

export async function getMatch(matchId) {
  return request(`/matches/${matchId}`);
}

export async function getCandidate(candidateId) {
  return request(`/candidates/${candidateId}`);
}

export async function getCandidateMatches(candidateId) {
  return request(`/candidates/${candidateId}/matches`);
}

export function pollMatch(matchId, onComplete, onError) {
  const INTERVAL_MS  = 3000;
  const MAX_ATTEMPTS = 60;   // 3 min timeout
  let attempts = 0;

  const id = setInterval(async () => {
    attempts++;
    if (attempts > MAX_ATTEMPTS) {
      clearInterval(id);
      onError('Analysis timed out after 3 minutes. Please try again.');
      return;
    }

    try {
      const { data, status } = await getMatch(matchId);
      if (status === 200) {
        clearInterval(id);
        onComplete(data);
      }
      // 202 = still processing, keep polling
    } catch (err) {
      if (err.status >= 400 && err.status < 500) {
        // 4xx — definitive failure, stop polling
        clearInterval(id);
        onError(err.message);
      }
      // 5xx or network error — transient, keep polling
    }
  }, INTERVAL_MS);

  return () => clearInterval(id);  // cancel function
}