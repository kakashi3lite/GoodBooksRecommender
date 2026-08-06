/**
 * 🧭 Navigation Sidebar Component Tests
 * Chain-of-Thought: Verify nav renders all routes and theme toggle dispatches
 */

import { configureStore } from '@reduxjs/toolkit'
import { fireEvent, render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import NavigationSidebar from '../../src/components/Navigation/NavigationSidebar'
import aiReducer from '../../src/stores/ai/aiSlice'
import dashboardReducer from '../../src/stores/dashboard/dashboardSlice'
import readingReducer from '../../src/stores/reading/readingSlice'
import userReducer from '../../src/stores/user/userSlice'

const createStore = () =>
    configureStore({
        reducer: {
            dashboard: dashboardReducer,
            ai: aiReducer,
            user: userReducer,
            reading: readingReducer
        }
    })

const renderSidebar = () => {
    const store = createStore()
    return {
        store,
        ...render(
            <Provider store={store}>
                <MemoryRouter>
                    <NavigationSidebar />
                </MemoryRouter>
            </Provider>
        )
    }
}

describe('NavigationSidebar', () => {
    it('renders all navigation destinations', () => {
        renderSidebar()
        expect(screen.getByText('Dashboard')).toBeInTheDocument()
        expect(screen.getByText('Discover')).toBeInTheDocument()
        expect(screen.getByText('Currently Reading')).toBeInTheDocument()
        expect(screen.getByText('Wishlist')).toBeInTheDocument()
        expect(screen.getByText('Reading Analytics')).toBeInTheDocument()
        expect(screen.getByText('Community')).toBeInTheDocument()
        expect(screen.getByText('Book News')).toBeInTheDocument()
    })

    it('links to real routes', () => {
        renderSidebar()
        const discoverLink = screen.getByRole('link', { name: /Discover/ })
        expect(discoverLink).toHaveAttribute('href', '/discover')
        const wishlistLink = screen.getByRole('link', { name: /Wishlist/ })
        expect(wishlistLink).toHaveAttribute('href', '/wishlist')
    })

    it('toggles the theme via the Dark Mode action', () => {
        const { store } = renderSidebar()
        const before = (store.getState() as any).dashboard.theme
        fireEvent.click(screen.getByText('Dark Mode'))
        const after = (store.getState() as any).dashboard.theme
        expect(after).not.toBe(before)
    })

    it('opens the AI assistant via Quick Recommendation', () => {
        const { store } = renderSidebar()
        fireEvent.click(screen.getByText('Quick Recommendation'))
        expect((store.getState() as any).ai.isOpen).toBe(true)
    })
})
