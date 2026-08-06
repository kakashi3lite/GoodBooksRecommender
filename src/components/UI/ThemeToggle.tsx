/**
 * 🌗 Theme Toggle Component
 * Chain-of-Thought: Toggle between light, dark, and auto themes
 * Memory: Theme preference persists via the Redux dashboard slice
 */

import { Moon, Sun } from 'lucide-react'
import React from 'react'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import { setTheme } from '../../stores/dashboard/dashboardSlice'

/**
 * ThemeToggle — cycles light → dark → auto.
 * Aesthetic: Animated sun/moon icons with a sliding indicator.
 */
const ThemeToggle: React.FC = () => {
  const dispatch = useAppDispatch()
  const theme = useAppSelector((state) => state.dashboard.theme)

  const cycleTheme = () => {
    const order: Array<'light' | 'dark' | 'auto'> = ['light', 'dark', 'auto']
    const next = order[(order.indexOf(theme) + 1) % order.length]
    dispatch(setTheme(next))
  }

  return (
    <button
      onClick={cycleTheme}
      className="relative inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
      aria-label={`Switch theme (currently ${theme})`}
      title={`Theme: ${theme}`}
    >
      {theme === 'dark' ? (
        <Moon className="w-4 h-4 text-blue-500" />
      ) : (
        <Sun className="w-4 h-4 text-yellow-500" />
      )}
      <span className="text-sm font-medium text-gray-700 dark:text-gray-200 capitalize">
        {theme}
      </span>
    </button>
  )
}

export default ThemeToggle
