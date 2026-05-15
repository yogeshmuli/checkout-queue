export const motionPresets = {
  fadeInDown: {
    initial: { opacity: 0, y: -10 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.5 },
  },
  fadeInLeft: {
    initial: { opacity: 0, x: -50 },
    animate: { opacity: 1, x: 0 },
    transition: { duration: 0.8, ease: 'easeOut' },
  },
  fadeInUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.8 },
  },
  heroVisualIn: {
    initial: { opacity: 0, scale: 0.8, rotate: -5 },
    animate: { opacity: 1, scale: 1, rotate: 0 },
    transition: { duration: 1, ease: 'easeOut' },
  },
  floatUpDown: {
    animate: { y: [-10, 10, -10] },
    transition: { repeat: Infinity, duration: 4, ease: 'easeInOut' },
  },
  floatDownUp: {
    animate: { y: [10, -10, 10] },
    transition: { repeat: Infinity, duration: 5, ease: 'easeInOut', delay: 1 },
  },
  buttonSpring: {
    whileHover: { scale: 1.05 },
    whileTap: { scale: 0.95 },
    transition: { type: 'spring', stiffness: 400, damping: 17 },
  },
  subtleButton: {
    whileHover: { scale: 1.03 },
    whileTap: { scale: 0.98 },
  },
};
