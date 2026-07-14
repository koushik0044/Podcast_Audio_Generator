import { describe, expect, it } from 'vitest';
import { API_BASE, audioUrl } from './api';

describe('audioUrl', () => {
  it('prefixes the API base onto the relative path the backend emits', () => {
    // This is the bug that broke playback: the backend serves audio itself and
    // returns "/audio/{job}/{line}". Fetching that bare resolves against the
    // frontend's origin and 404s.
    expect(audioUrl('/audio/abc-123/0')).toBe(`${API_BASE}/audio/abc-123/0`);
  });

  it('leaves absolute URLs alone', () => {
    const url = 'https://cdn.example.com/clip.mp3';
    expect(audioUrl(url)).toBe(url);
  });
});

describe('API_BASE', () => {
  it('points somewhere real and has no trailing slash', () => {
    expect(API_BASE).toMatch(/^https?:\/\//);
    expect(API_BASE.endsWith('/')).toBe(false);
  });
});
