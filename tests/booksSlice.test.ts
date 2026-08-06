/**
 * 📚 Books Slice — Static-Host Resilience Tests
 * Chain-of-Thought: On Cloudflare Pages (no backend), /api/* requests hit the
 * SPA fallback and return the index.html document with HTTP 200. axios would
 * surface that HTML string as `response.data`. These tests lock in the
 * defensive validation so reducers never crash on a non-array payload.
 */

import { configureStore } from '@reduxjs/toolkit'
import axios from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import booksReducer, { fetchRecommendations } from '../src/stores/books/booksSlice'

vi.mock('axios')

const createStore = () =>
    configureStore({
        reducer: {
            books: booksReducer
        }
    })

describe('booksSlice resilience to static-host fallback responses', () => {
    let store: ReturnType<typeof createStore>

    beforeEach(() => {
        store = createStore()
        vi.mocked(axios.get).mockReset()
    })

    it('fetchRecommendations never yields a non-array when the API returns HTML (SPA fallback)', async () => {
        // Simulate Cloudflare Pages `_redirects` fallback: /api/* -> index.html (200)
        vi.mocked(axios.get).mockResolvedValue({
            data: '<!DOCTYPE html><html><body>index.html</body></html>'
        })

        await store.dispatch(fetchRecommendations({ limit: 5 }) as any)

        const state = store.getState().books
        expect(Array.isArray(state.recommendations)).toBe(true)
        expect(state.recommendations).toEqual([])
        // Loading must be cleared so the UI never sticks on a spinner
        expect(state.loading).toBe(false)
    })

    it('fetchRecommendations keeps a real array payload intact', async () => {
        const books = [
            { id: 'b-1', title: 'Dune', authors: 'Frank Herbert', rating: 4.3, genres: ['Science Fiction'] }
        ]
        vi.mocked(axios.get).mockResolvedValue({ data: books })

        await store.dispatch(fetchRecommendations({ limit: 5 }) as any)

        const state = store.getState().books
        expect(state.recommendations).toEqual(books)
        expect(state.lastFetched).toBeTruthy()
    })
})
