import { motion } from 'framer-motion';

function ErrorPage({ errorMessage, onReset }) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center px-6">
      <motion.h2
        initial={{ opacity: 0 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="text-white text-3xl font-bold mb-4"
      >
        An Error Occurred
      </motion.h2>

      {/* Rendered as wrapping prose, not character-by-character: this now shows
          the backend's real error, which can be a long sentence. */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4, duration: 0.6 }}
        className="text-white text-lg text-center max-w-xl opacity-80 break-words"
      >
        {errorMessage}
      </motion.p>

      {onReset && (
        <motion.button
          onClick={onReset}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7, duration: 0.5 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          className="mt-8 bg-transparent opacity-70 text-white border border-white rounded-md px-6 py-3"
        >
          Try another topic
        </motion.button>
      )}
    </div>
  );
}

export default ErrorPage;