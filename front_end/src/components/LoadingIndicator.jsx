import React from 'react';
import { motion } from 'framer-motion';

const LoadingIndicator = ({
  isDownloading,
  text,
  messageContainer,
  messageChild,
}) => {
  return (
    isDownloading && (
      <div className="relative overflow-hidden text-sm leading-6 text-white">
        <motion.p
          variants={messageContainer}
          initial="hidden"
          animate="visible"
          className="text-white text-xl"
        >
          {text.map((char, index) => (
            <motion.span key={char + '-' + index} variants={messageChild}>
              {char === ' ' ? '\u00A0' : char}
            </motion.span>
          ))}
        </motion.p>
      </div>
    )
  );
};

export default LoadingIndicator;