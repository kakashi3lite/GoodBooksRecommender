/**
 * ❤️ Wishlist Component Tests
 * Chain-of-Thought: Verify the saved-for-later shelf renders saved books and
 * that "Start Reading" actually starts the book (a dead CTA is a trust-killer).
 */

import { configureStore } from '@reduxjs/toolkit'
import { fireEvent, render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import Wishlist from '../../src/components/Features/Wishlist'
import { BOOK_CATALOG } from '../../src/data/bookCatalog'
import booksReducer from '../../src/stores/books/booksSlice'
import readingReducer from '../../src/stores/reading/readingSlice'
import userReducer, { toggleFavorite } from '../../src/stores/user/userSlice'

const book = BOOK_CATALOG[0]

const createStore = () =>
    configureStore({
        reducer: {
            user: userReducer,
            books: booksReducer,
            reading: readingReducer
        }
    })

const renderWishlist = (store: ReturnType<typeof createStore>) =>
    render(
        <Provider store={store}>
            <MemoryRouter>
                <Wishlist />
            </MemoryRouter>
        </Provider>
    )

describe('Wishlist', () => {
    let store: ReturnType<typeof createStore>

    beforeEach(() => {
        store = createStore()
    })

    it('shows an empty state when nothing is saved', () => {
        renderWishlist(store)
        expect(screen.getByText(/Nothing saved yet/i)).toBeInTheDocument()
    })

    it('renders saved books from the catalog with their real cover', () => {
        store.dispatch(toggleFavorite(book.id))
        renderWishlist(store)
        // The card heading carries the title (BookCover also renders it, so
        // target the heading role to stay unambiguous).
        expect(screen.getByRole('heading', { name: book.title })).toBeInTheDocument()
        // The cover image (real Open Library URL) must be in the document —
        // the generated-art-only regression was covers never loading here.
        const cover = document.querySelector(`img[src="${book.cover_url}"]`)
        expect(cover).not.toBeNull()
    })

    it('starts a book when "Start Reading" is clicked', () => {
        store.dispatch(toggleFavorite(book.id))
        renderWishlist(store)
        fireEvent.click(screen.getByRole('button', { name: /start reading/i }))

        const reading = (store.getState() as any).reading
        expect(reading.currentlyReading).toHaveLength(1)
        expect(reading.currentlyReading[0].bookId).toBe(book.id)
        expect(reading.currentlyReading[0].book?.title).toBe(book.title)
    })
})
