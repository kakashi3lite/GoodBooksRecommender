/**
 * 📱 Mobile Bottom Navigation — the primary thumb-zone nav (< 768px).
 * Chain-of-Thought: a reader's most-used surfaces (Home, Discover, Shelf)
 * belong in the thumb zone as a persistent bottom bar — the standard mobile
 * pattern that eliminates hunting for buttons in a drawer. "More" opens the
 * off-canvas drawer for everything else (remaining routes + account + tools).
 * Hidden on ≥ 768px (desktop/iPad use the sidebar).
 */

import { BookOpen, Compass, Home as HomeIcon, Menu } from 'lucide-react'
import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import { toggleMobileNav } from '../../stores/dashboard/dashboardSlice'

const MobileBottomNav: React.FC = () => {
    const dispatch = useAppDispatch()
    const activeCount = useAppSelector(
        (state) => state.reading.currentlyReading.filter((e) => e.finishedAt === null).length
    )
    const navOpen = useAppSelector((state) => state.dashboard.mobileNavOpen)

    const tabs = [
        { to: '/', label: 'Home', icon: HomeIcon, end: true },
        { to: '/discover', label: 'Discover', icon: Compass },
        {
            to: '/reading',
            label: 'Shelf',
            icon: BookOpen,
            badge: activeCount > 0 ? String(activeCount) : undefined
        }
    ]

    return (
        <nav className="mobile-bottom-nav" aria-label="Primary navigation">
            {tabs.map((tab) => (
                <NavLink
                    key={tab.to}
                    to={tab.to}
                    end={tab.end}
                    className={({ isActive }) => `mobile-bottom-tab${isActive ? ' active' : ''}`}
                >
                    <span className="relative">
                        <tab.icon className="w-5 h-5" />
                        {tab.badge && <span className="mobile-bottom-badge">{tab.badge}</span>}
                    </span>
                    <span className="mobile-bottom-label">{tab.label}</span>
                </NavLink>
            ))}

            <button
                type="button"
                onClick={() => dispatch(toggleMobileNav())}
                className={`mobile-bottom-tab${navOpen ? ' active' : ''}`}
                aria-label="More menu"
                aria-expanded={navOpen}
            >
                <Menu className="w-5 h-5" />
                <span className="mobile-bottom-label">More</span>
            </button>
        </nav>
    )
}

export default MobileBottomNav
