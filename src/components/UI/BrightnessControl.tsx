/**
 * 💡 Brightness Control Component
 * Chain-of-Thought: Adjust dashboard brightness for comfortable reading
 * Memory: Brightness preference persists via the Redux dashboard slice
 */

import { Sun, SunDim } from 'lucide-react'
import React from 'react'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import { setBrightness } from '../../stores/dashboard/dashboardSlice'

/**
 * BrightnessControl — slider that adjusts the dashboard brightness.
 * Applies a CSS filter on the app shell so it feels like a reader's
 * warm-light dimming control.
 */
const BrightnessControl: React.FC = () => {
    const dispatch = useAppDispatch()
    const brightness = useAppSelector((state) => state.dashboard.brightness)

    const handleChange = (value: number) => {
        dispatch(setBrightness(value))
        // Apply a brightness filter to the app root for immediate visual feedback
        const root = document.querySelector('.app-shell') as HTMLElement | null
        if (root) {
            root.style.filter = `brightness(${value / 100})`
        }
    }

    return (
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-gray-100 dark:bg-gray-800">
            <SunDim className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <input
                type="range"
                min={40}
                max={100}
                value={brightness}
                onChange={(e) => handleChange(Number(e.target.value))}
                className="w-24 h-1.5 accent-blue-600 cursor-pointer"
                aria-label="Dashboard brightness"
            />
            <Sun className="w-4 h-4 text-yellow-500" />
        </div>
    )
}

export default BrightnessControl
