import React from 'react';
import { motion } from 'framer-motion';

const TextDisplay = ({
  isTextVisible,
  items,
  currentItemIndex,
  textContainerVariants,
  textChildVariants,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.5, duration: 0.7 }}
      className="relative bg-transparent border border-white border-opacity-20 rounded-md p-4 text-white text-center text-xl w-96 h-96 flex items-center justify-center whitespace-normal"
    >
      {isTextVisible && items[currentItemIndex] && (
        <motion.div
          key={currentItemIndex}
          variants={textContainerVariants}
          initial="hidden"
          animate="visible"
        >
          {items[currentItemIndex].text
            .split(/(\s+)/)
            .map((word, index) => (
              <motion.span
                key={`${word}-${index}`}
                variants={textChildVariants}
                className="inline-block"
              >
                {word === ' ' ? '\u00A0' : word}
              </motion.span>
            ))}
        </motion.div>
      )}
    </motion.div>
  );
};

export default TextDisplay;