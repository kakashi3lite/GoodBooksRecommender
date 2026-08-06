/**
 * 🎨 Tailwind CSS Configuration
 * Chain-of-Thought: Scan all source files for utility classes
 * Memory: Design tokens aligned with the existing design-system.css
 * Forward-Thinking: Dark mode via class strategy, driven by Redux theme state
 */

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx}',
    './dashboard/**/*.{html,css}'
  ],
  // Class-based dark mode so Redux theme state can toggle it dynamically
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Aligned with the design-system.css tokens
        primary: {
          DEFAULT: '#3b82f6',
          dark: '#1d4ed8'
        },
        secondary: '#8b5cf6',
        accent: '#06b6d4',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444'
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        serif: ['Crimson Text', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'monospace']
      },
      boxShadow: {
        'glow-blue': '0 0 20px rgba(59, 130, 246, 0.35)',
        'glow-purple': '0 0 20px rgba(139, 92, 246, 0.35)',
        'card': '0 10px 30px -10px rgba(0, 0, 0, 0.2)'
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        }
      }
    }
  },
  plugins: []
}
