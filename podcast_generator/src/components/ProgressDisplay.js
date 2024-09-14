import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ProgressDisplay({ jobId }) {
  const [progress, setProgress] = useState([]);
  const [status, setStatus] = useState('started');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let intervalId;

    const fetchProgress = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/progress/${jobId}`);
        const data = response.data;
        setStatus(data.status);
        setProgress(data.progress);
        if (data.result) {
          setResult(data.result);
        }
        if (data.error) {
          setError(data.error);
        }
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(intervalId);
        }
      } catch (err) {
        console.error('Error fetching progress:', err);
        setError('Failed to fetch progress.');
        clearInterval(intervalId);
      }
    };

    // Poll every 5 seconds
    intervalId = setInterval(fetchProgress, 5000);
    // Fetch immediately on mount
    fetchProgress();

    return () => clearInterval(intervalId);
  }, [jobId]);

  return (
    <div>
      <h2>Job ID: {jobId}</h2>
      <h3>Status: {status}</h3>
      <div>
        {progress.map((message, index) => (
          <div key={index}>
            {typeof message === 'string' ? (
              <p>{message}</p>
            ) : message.type === 'audio' ? (
              <div>
                <p>Line {message.line_number} Audio:</p>
                <audio controls>
                  <source src={message.audio_url} type="audio/mpeg" />
                  Your browser does not support the audio element.
                </audio>
              </div>
            ) : message.type === 'error' ? (
              <p style={{ color: 'red' }}>{message.message}</p>
            ) : null}
          </div>
        ))}
      </div>
      {result && (
        <div>
          <h3>Final Script:</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
      {error && (
        <div>
          <h3 style={{ color: 'red' }}>Error:</h3>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}

export default ProgressDisplay;
