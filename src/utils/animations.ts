/**
 * 🎬 Animation Utilities
 * Chain-of-Thought: Consistent animation patterns across the dashboard
 * Memory: Reusable animation variants for component consistency
 * Forward-Thinking: Extensible animations for future UI elements
 */

import { Variants } from 'framer-motion';

// Framer Motion animation variants
export const fadeInOut: Variants = {
  initial: { 
    opacity: 0 
  },
  animate: { 
    opacity: 1,
    transition: { duration: 0.3 } 
  },
  exit: { 
    opacity: 0,
    transition: { duration: 0.3 } 
  }
}

export const slideInFromLeft: Variants = {
  initial: { 
    x: -50, 
    opacity: 0 
  },
  animate: { 
    x: 0, 
    opacity: 1,
    transition: { duration: 0.4, ease: "easeOut" } 
  },
  exit: { 
    x: -50, 
    opacity: 0,
    transition: { duration: 0.4, ease: "easeOut" } 
  }
}

export const slideInFromRight: Variants = {
  initial: { 
    x: 50, 
    opacity: 0 
  },
  animate: { 
    x: 0, 
    opacity: 1,
    transition: { duration: 0.4, ease: "easeOut" } 
  },
  exit: { 
    x: 50, 
    opacity: 0,
    transition: { duration: 0.4, ease: "easeOut" } 
  }
}

export const slideInFromBottom: Variants = {
  initial: { 
    y: 50, 
    opacity: 0 
  },
  animate: { 
    y: 0, 
    opacity: 1,
    transition: { duration: 0.4, ease: "easeOut" } 
  },
  exit: { 
    y: 50, 
    opacity: 0,
    transition: { duration: 0.4, ease: "easeOut" } 
  }
}

export const slideInFromTop: Variants = {
  initial: { 
    y: -50, 
    opacity: 0 
  },
  animate: { 
    y: 0, 
    opacity: 1,
    transition: { duration: 0.4, ease: "easeOut" } 
  },
  exit: { 
    y: -50, 
    opacity: 0,
    transition: { duration: 0.4, ease: "easeOut" } 
  }
}

export const popIn: Variants = {
  initial: { 
    scale: 0.8, 
    opacity: 0 
  },
  animate: { 
    scale: 1, 
    opacity: 1,
    transition: { type: "spring", damping: 12, stiffness: 200 } 
  },
  exit: { 
    scale: 0.8, 
    opacity: 0,
    transition: { duration: 0.2 } 
  }
}

export const pageTransition: Variants = {
  initial: { 
    opacity: 0 
  },
  animate: { 
    opacity: 1,
    transition: { duration: 0.5, when: "beforeChildren", staggerChildren: 0.1 } 
  },
  exit: { 
    opacity: 0,
    transition: { duration: 0.3, when: "afterChildren", staggerChildren: 0.05 } 
  }
}

export const staggerContainer: Variants = {
  animate: {
    transition: {
      staggerChildren: 0.08
    }
  }
}

export const staggerItem: Variants = {
  initial: { 
    y: 20, 
    opacity: 0 
  },
  animate: { 
    y: 0, 
    opacity: 1,
    transition: { duration: 0.4 } 
  },
  exit: { 
    y: 20, 
    opacity: 0,
    transition: { duration: 0.3 } 
  }
}

// GPU-accelerated card hover animation
export const bookCardHover: Variants = {
  initial: {
    scale: 1,
    y: 0,
    rotateY: 0,
    boxShadow: "0px 2px 8px rgba(0, 0, 0, 0.1)"
  },
  hover: {
    scale: 1.03,
    y: -5,
    rotateY: 5,
    boxShadow: "0px 10px 20px rgba(0, 0, 0, 0.2), 0px 0px 15px rgba(0, 212, 255, 0.3)",
    transition: { duration: 0.3, ease: "easeOut" }
  },
  tap: {
    scale: 0.98,
    transition: { duration: 0.1 }
  }
}
