import React, { useState } from 'react';
import axios from 'axios';
import ProgressDisplay from './ProgressDisplay';

function ScriptGenerator() {
  const [topic, setTopic] = useState('');
  const [jobId, setJobId] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topic) {
      alert('Please enter a topic.');
      return;
    }

    try {
      const response = await axios.post('http://localhost:8000/generate-script', { topic });
      setJobId(response.data.job_id);
    } catch (error) {
      console.error('Error initiating script generation:', error);
      alert('Failed to start script generation.');
    }
  };

  return (
    <div>
      {!jobId ? (
        <form onSubmit={handleSubmit}>
          <label>
            Enter Topic:
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </label>
          <button type="submit">Generate Script</button>
        </form>
      ) : (
        <ProgressDisplay jobId={jobId} />
      )}
    </div>
  );
}

export default ScriptGenerator;
