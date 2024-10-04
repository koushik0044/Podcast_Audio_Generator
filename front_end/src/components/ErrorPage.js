import { motion } from 'framer-motion';

function ErrorPage({ errorMessage }) {
  const text = errorMessage;
  const letters = text.split("");

  const container = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,  // Delay between each letter's appearance
        delayChildren: 0.2,     // Delay before starting the animation
      },
    },
  };

  const child = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
  };

  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center">
      {/* Error Message Header */}
      <motion.h2
        initial={{ opacity: 0 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="text-white text-3xl font-bold mb-4"
      >
        An Error Occurred
      </motion.h2>

      {/* Character-by-character animation for the errorMessage */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="visible"
        className="text-white text-xl flex"
      >
        {letters.map((char, index) => (
          <motion.span
            key={char + "-" + index}
            variants={child}
            className="inline-block"
          >
            {char === " " ? "\u00A0" : char}
          </motion.span>
        ))}
      </motion.div>
    </div>
  );
}

export default ErrorPage;