import React from 'react';
import { motion } from 'framer-motion';
import Siriwave from 'react-siriwave';

const AudioControls = ({
  handlePlayPause,
  isPlaying,
  isDownloading,
  handleDownload,
  siriWaveConfigs,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -100 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, duration: 0.7 }}
      className="flex bg-white bg-opacity-20 backdrop-filter backdrop-blur-lg rounded-xl items-center justify-between w-full p-4"
    >
      {/* Play/Pause Button */}
      <motion.div
        initial={{ opacity: 0, x: -100 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.3, duration: 0.7 }}
      >
        <motion.button
          onClick={handlePlayPause}
          className={`bg-white bg-opacity-20 backdrop-filter backdrop-blur-lg rounded-full p-4 focus:outline-none hover:bg-opacity-30 ${
            isDownloading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
          aria-label={isPlaying ? 'Pause audio' : 'Play audio'}
          disabled={isDownloading}
          whileHover={{ scale: 1.1, rotate: 360 }}
          whileTap={{ scale: 0.9 }}
        >
          {isPlaying ? (
            // Pause Icon with Framer Motion SVG
            <motion.svg
              initial={{ opacity: 0, rotate: 90 }}
              animate={{ opacity: 1, rotate: 0 }}
              transition={{ duration: 0.2 }}
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <motion.path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 9v6m4-6v6"
              />
            </motion.svg>
          ) : (
            // Play Icon with Framer Motion SVG
            <motion.svg
              initial={{ opacity: 0, rotate: -90 }}
              animate={{ opacity: 1, rotate: 0 }}
              transition={{ duration: 0.3 }}
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <motion.path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14.752 11.168l-6.4-3.692A1 1 0 007 8.382v7.236a1 1 0 001.352.936l6.4-3.692a1 1 0 000-1.736z"
              />
            </motion.svg>
          )}
        </motion.button>
      </motion.div>

      {/* SiriWave Component */}
      <div className="flex-grow mx-4">
        <div className="w-full h-24 flex justify-center items-center">
          <Siriwave {...siriWaveConfigs} />
        </div>
      </div>

      {/* Download Button */}
      <motion.div
        initial={{ opacity: 0, x: 100 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.3, duration: 0.7 }}
      >
        <motion.button
          onClick={handleDownload}
          className={`bg-white bg-opacity-20 backdrop-filter backdrop-blur-lg rounded-full p-4 focus:outline-none hover:bg-opacity-30 ${
            isDownloading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
          aria-label="Download audio"
          disabled={isDownloading}
          whileHover={{ scale: 1.1, rotate: 360 }}
          whileTap={{ scale: 0.9 }}
          animate={isDownloading ? { scale: 1.05, opacity: 0.5 } : {}}
          transition={{ duration: 0.3 }}
        >
          {/* Download Icon with Framer Motion */}
          <motion.svg
            initial={{ opacity: 0, y: -10 }} // Start from above with 0 opacity
            animate={{ opacity: 1, y: 0 }} // Fade in and slide into place
            transition={{ duration: 0.3 }} // Smooth transition
            className="w-6 h-6 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <motion.path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v8m0 0l-3-3m3 3l3-3m-6 6h6"
            />
          </motion.svg>
        </motion.button>
      </motion.div>
    </motion.div>
  );
};

export default AudioControls;