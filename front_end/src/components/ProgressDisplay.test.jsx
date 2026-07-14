import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as api from '../api';
import ProgressDisplay from './ProgressDisplay';

// lottie-web touches a canvas at import time, which jsdom does not provide.
vi.mock('lottie-react', () => ({ default: () => <div data-testid="lottie" /> }));

// AudioDisplay drives the Web Audio API, which jsdom does not implement.
// Stub it: these tests are about what ProgressDisplay decides to render.
vi.mock('./AudioDisplay', () => ({
  default: ({ items, isComplete }) => (
    <div data-testid="player">
      player: {items.length} lines, complete={String(isComplete)}
    </div>
  ),
}));

const job = (overrides) => ({
  data: { status: 'started', progress: [], result: null, error: null, ...overrides },
});

const audioEvent = (i) => ({
  type: 'audio',
  line_number: i,
  audio_url: `/audio/job-1/${i}`,
  text: `line ${i}`,
  no_of_dialogues: 4,
});

beforeEach(() => {
  vi.restoreAllMocks();
});

describe('ProgressDisplay', () => {
  it('shows the player as soon as the first line lands, before the job completes', async () => {
    // The whole point of progressive playback: don't wait for 'completed'.
    vi.spyOn(api, 'getProgress').mockResolvedValue(
      job({ status: 'started', progress: [audioEvent(0)] })
    );

    render(<ProgressDisplay jobId="job-1" />);

    const player = await screen.findByTestId('player');
    expect(player).toHaveTextContent('1 lines');
    expect(player).toHaveTextContent('complete=false');
  });

  it('accumulates audio lines into the playlist', async () => {
    vi.spyOn(api, 'getProgress').mockResolvedValue(
      job({
        status: 'completed',
        progress: [audioEvent(0), audioEvent(1), audioEvent(2)],
      })
    );

    render(<ProgressDisplay jobId="job-1" />);

    const player = await screen.findByTestId('player');
    expect(player).toHaveTextContent('3 lines');
    expect(player).toHaveTextContent('complete=true');
  });

  it('surfaces the backend error instead of hanging on a failed job', async () => {
    // Previously a 'failed' status only cleared the poll interval, so the UI
    // froze on the last message and looked identical to a slow job.
    vi.spyOn(api, 'getProgress').mockResolvedValue(
      job({ status: 'failed', error: 'Groq rate limit reached' })
    );

    render(<ProgressDisplay jobId="job-1" />);

    expect(await screen.findByText(/Groq rate limit reached/)).toBeInTheDocument();
  });

  it('reports an unknown job id (404) rather than spinning forever', async () => {
    const notFound = new Error('Not Found');
    notFound.response = { status: 404 };
    vi.spyOn(api, 'getProgress').mockRejectedValue(notFound);

    render(<ProgressDisplay jobId="ghost" />);

    expect(await screen.findByText(/no longer exists/i)).toBeInTheDocument();
  });

  it('reports an unreachable backend', async () => {
    vi.spyOn(api, 'getProgress').mockRejectedValue(new Error('Network Error'));

    render(<ProgressDisplay jobId="job-1" />);

    expect(await screen.findByText(/Lost contact with the backend/i)).toBeInTheDocument();
  });

  it('renders progress messages while working', async () => {
    vi.spyOn(api, 'getProgress').mockResolvedValue(
      job({
        progress: [
          { type: 'string', status: 'News-Agent', message: 'Searching the internet' },
        ],
      })
    );

    render(<ProgressDisplay jobId="job-1" />);

    await waitFor(() => {
      expect(screen.queryByTestId('player')).not.toBeInTheDocument();
    });
    expect(document.body).toHaveTextContent(/Searching the internet/);
  });
});
