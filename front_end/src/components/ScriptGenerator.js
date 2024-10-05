import React, { useState } from 'react';
import axios from 'axios';
import ProgressDisplay from './ProgressDisplay';
import { motion } from "framer-motion";

function ScriptGenerator() {
  const [topic, setTopic] = useState('');
  const [jobId, setJobId] = useState(null);

  const text = "Podcast Audio Generator";
  const letters = text.split("");

  const container = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,  // Delay between each letter's appearance
        duration: 0.7,          // Total duration for all letters
        delay: 0.2,             // Delay before starting the animation
      },
    },
  };

  const child = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topic) {
      alert('Please enter a topic.');
      return;
    }

    try {
      const response = await axios.post('https://podcast-audio-generator.onrender.com/generate-script', { topic });
      setJobId(response.data.job_id);
    } catch (error) {
      console.error('Error initiating script generation:', error);
      alert('Failed to start script generation.');
    }
  };

  return (
    <div>
      {!jobId ? (
        <div className="absolute inset-0 flex items-center justify-center">
        <form className="flex flex-col items-center space-y-4" onSubmit={handleSubmit}>
        <motion.div
              initial="hidden"
              animate="visible"
              variants={container}
            >
            <h1 className="text-white opacity-70 text-4xl font-bold">
              {letters.map((char, index) => (
                <motion.span key={char + "-" + index} variants={child}>
                  {char === " " ? "\u00A0" : char}
                </motion.span>
              ))}
            </h1>
          </motion.div>
            <motion.div
            initial={{ opacity: 0, x: -100}}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.8 }}
          >
          {/* Transparent Input Box */}
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Enter Topic"
            className="bg-transparent opacity-70 text-white border border-white rounded-md p-3 placeholder-white focus:outline-none focus:ring-2 focus:ring-white w-80"
          />
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: 100}}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.8 }}
          >
          {/* Submit Button with hover invert effect */}
          <motion.button
  type="submit"
  className="bg-transparent opacity-70 text-white border border-white rounded-md px-6 py-3"
  whileHover={{
    scale: 1.1,                // Slightly scale up on hover
    backgroundColor: "rgba(255, 255, 255, 0.7)",  // Change background on hover
    color: "#ffffff",           // Change text color on hover
  }}
  whileTap={{ scale: 0.95 }}    // Scale down slightly on press
  transition={{
    duration: 0.1,              // Transition duration for the animation
    ease: "easeInOut",
  }}
>
  Generate
</motion.button>
          </motion.div>

        </form>
      </div>
      ) : (
        <ProgressDisplay jobId={jobId} />
      )}
    </div>
  );
}

export default ScriptGenerator;
