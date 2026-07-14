import axios from 'axios';

// Vite inlines this at build time, so deploys must set it as a build env var.
export const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const startJob = (topic) =>
  axios.post(`${API_BASE}/generate-script`, { topic });

export const getProgress = (jobId) =>
  axios.get(`${API_BASE}/progress/${jobId}`);

/**
 * The backend serves audio itself now and emits a *relative* path
 * ("/audio/{job_id}/{line}"). Passing that straight to fetch() would resolve it
 * against the frontend's origin and 404, so every audio fetch must go through
 * here. Absolute URLs are passed through untouched.
 */
export const audioUrl = (path) =>
  /^https?:\/\//i.test(path) ? path : `${API_BASE}${path}`;
