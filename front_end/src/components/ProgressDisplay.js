// ProgressDisplay.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import AudioDisplay from './AudioDisplay';
import ErrorPage from './ErrorPage';
import Lottie from 'lottie-react';
import deficon from '../icons/default-icon.json';
import newsIcon from '../icons/new-agent-icon.json';
import writerIcon from '../icons/write-agent-icon.json';
import ttsIcon from '../icons/TTS-icon.json';
import { motion } from "framer-motion";

function ProgressDisplay({ jobId }) {
  const [status, setStatus] = useState('started');
  const [currentMessage, setCurrentMessage] = useState('');
  const [audioMap, setAudioMap] = useState([]);
  const [iconKey, setIconKey] = useState('default');
  const [error, setError] = useState(false);
  const [processedMessageIds, setProcessedMessageIds] = useState(new Set());

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
  
    const fetchProgress = async () => {
      try {
        const response = await axios.get(`https://podcast-audio-generator.onrender.com/progress/${jobId}`);
        const data = response.data;
        setStatus(data.status);
  
        if (data.progress && data.progress.length > 0) {
          const lastMessage = data.progress[data.progress.length - 1];
  
          if (lastMessage.type === 'string') {
            setCurrentMessage(lastMessage.message);
            // Change icon when new message arrives
            setIconKey(lastMessage.status);
          } else if (lastMessage.type === 'audio') {
            setCurrentMessage(`Audio for dialogue ${lastMessage.line_number + 1} out of ${lastMessage.no_of_dialogues} has been generated...`);
            // Change icon when processing audio
            setIconKey('TTS');
          } else if (lastMessage.type === 'error') {
            setError(true);
            clearInterval(intervalId);
          }
  
          // Reconstruct audioMap from all audio messages
          const audioMessages = data.progress.filter(msg => msg.type === 'audio');
          const audioItems = audioMessages.map(msg => ({
            audioUrl: msg.audio_url,
            text: msg.text,
          }));
          setAudioMap(audioItems);
        }
  
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(intervalId);
        }
      } catch (err) {
        console.error('Error fetching progress:', err);
        setError(true);
        clearInterval(intervalId);
      }
    };
  
    // Poll every 2 seconds
    intervalId = setInterval(fetchProgress, 2000);
    // Fetch immediately on mount
    fetchProgress();
  
    return () => clearInterval(intervalId);
  }, [jobId]);

  if (error) {
    return <ErrorPage errorMessage='I might have Ran out of Credits , Please Come Back Tommorow' />;
  }

  // If status is 'completed', render AudioDisplay component
  if (status === 'completed') {
    return (<div className="absolute inset-0 flex items-center justify-center">
      <AudioDisplay items={audioMap} />
    </div>);
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
