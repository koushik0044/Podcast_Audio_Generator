// ProgressDisplay.jsx
import React, { useState, useEffect } from 'react';
import { getProgress } from '../api';
import AudioDisplay from './AudioDisplay';
import ErrorPage from './ErrorPage';
import Lottie from 'lottie-react';
import deficon from '../icons/default-icon.json';
import newsIcon from '../icons/new-agent-icon.json';
import writerIcon from '../icons/write-agent-icon.json';
import ttsIcon from '../icons/TTS-icon.json';
import { motion } from "framer-motion";

function ProgressDisplay({ jobId, onReset }) {
  const [status, setStatus] = useState('started');
  const [currentMessage, setCurrentMessage] = useState('');
  const [audioMap, setAudioMap] = useState([]);
  const [iconKey, setIconKey] = useState('default');
  const [error, setError] = useState('');

  // Splitting the currentMessage into individual characters
  const letters = currentMessage.split("");

  // Variants for the parent container to stagger children animations (characters)
  const messageContainer = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,  // Delay between each character's appearance
        delayChildren: 0.2,     // Delay before starting the animation
      },
    },
  };

  // Variants for individual characters
  const messageChild = {
    hidden: { opacity: 0, y: -10 },  // Start with opacity 0 and slightly above the position
    visible: { opacity: 1, y: 0 },   // Fade in and slide to the correct position
  };

  // Icons array to change icons when a new message arrives
  const agentIcons = {
    'News-Agent': newsIcon,
    'Writer-Agent': writerIcon,
    'TTS': ttsIcon,
    'default' : deficon
  };

  useEffect(() => {
    let intervalId;
    let cancelled = false;

    const stop = () => clearInterval(intervalId);

    const fetchProgress = async () => {
      try {
        const { data } = await getProgress(jobId);
        if (cancelled) return;

        setStatus(data.status);

        if (data.progress && data.progress.length > 0) {
          const lastMessage = data.progress[data.progress.length - 1];

          if (lastMessage.type === 'string') {
            setCurrentMessage(lastMessage.message);
            setIconKey(lastMessage.status);
          } else if (lastMessage.type === 'audio') {
            setCurrentMessage(
              `Audio for dialogue ${lastMessage.line_number + 1} out of ${lastMessage.no_of_dialogues} has been generated...`
            );
            setIconKey('TTS');
          }

          // Rebuild the playlist from every audio event seen so far. The player
          // consumes this as it grows, so lines play while the rest generate.
          setAudioMap(
            data.progress
              .filter((msg) => msg.type === 'audio')
              .map((msg) => ({ audioUrl: msg.audio_url, text: msg.text }))
          );
        }

        if (data.status === 'failed') {
          // Previously this only cleared the interval, so the UI hung on the
          // last message forever and a failure looked exactly like a slow job.
          setError(data.error || 'Generation failed.');
          stop();
        } else if (data.status === 'completed') {
          stop();
        }
      } catch (err) {
        if (cancelled) return;
        console.error('Error fetching progress:', err);
        // An unknown job id is now a 404 (it used to be a 200 with an error body).
        setError(
          err.response?.status === 404
            ? 'That job no longer exists. It may have expired.'
            : 'Lost contact with the backend. Is it still running?'
        );
        stop();
      }
    };

    intervalId = setInterval(fetchProgress, 2000);
    fetchProgress();

    return () => {
      cancelled = true;
      stop();
    };
  }, [jobId]);

  if (error) {
    return <ErrorPage errorMessage={error} onReset={onReset} />;
  }

  // Show the player as soon as the first line's audio exists, rather than
  // waiting for the whole job. The backend streams audio per line; waiting for
  // 'completed' threw that away and left the user on a spinner for the duration.
  if (audioMap.length > 0) {
    return (
      <div className="absolute inset-0 flex items-center justify-center">
        <AudioDisplay
          items={audioMap}
          isComplete={status === 'completed'}
          onReset={onReset}
        />
      </div>
    );
  }

  // Get the current icon
  const CurrentIcon = agentIcons[iconKey] || deficon;

  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center">
      {/* Animated icon */}
      <motion.div
        key={CurrentIcon} // Ensures animation triggers when the icon changes
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.7 }} // Icon fade-in duration
        className="text-white text-6xl mb-4"
      >
        <Lottie animationData={CurrentIcon} style={{ width: 100, height: 100 }} loop={true} />
      </motion.div>

      {/* Character-by-character message animation */}
      <motion.p
        key={currentMessage}  // Ensure animation restarts when message changes
        variants={messageContainer}
        initial="hidden"
        animate="visible"
        className="text-white text-xl"
      >
        {letters.map((char, index) => (
          <motion.span key={char + "-" + index} variants={messageChild}>
            {char === " " ? "\u00A0" : char}
          </motion.span>
        ))}
      </motion.p>
    </div>
  );
}

export default ProgressDisplay;
