/**
 * 📝 Notes Slice Tests
 * Chain-of-Thought: Verify note CRUD with offline-friendly fallback
 */

import { configureStore } from '@reduxjs/toolkit'
import { describe, expect, it, vi } from 'vitest'
import reducer, {
  createNote,
  deleteNote,
  selectNotesByBook,
  type NotesSliceState
} from '../src/stores/features/notesSlice'

// Mock the API so createNote falls back to local persistence
vi.mock('../src/utils/api', () => ({
  NotesService: {
    getAllNotes: vi.fn().mockRejectedValue(new Error('down')),
    createNote: vi.fn().mockRejectedValue(new Error('down')),
    updateNote: vi.fn().mockRejectedValue(new Error('down')),
    deleteNote: vi.fn().mockRejectedValue(new Error('down'))
  }
}))

const createStore = () =>
  configureStore({
    reducer: {
      notes: reducer
    }
  })

describe('notesSlice', () => {
  it('creates a note locally when the backend is unavailable', async () => {
    const store = createStore()
    await store.dispatch(
      createNote({
        bookId: 'b1',
        bookTitle: 'Atomic Habits',
        title: 'Key idea',
        content: 'Tiny changes, remarkable results',
        tags: ['habits']
      }) as any
    )

    const state = store.getState().notes as NotesSliceState
    expect(state.items).toHaveLength(1)
    expect(state.items[0].bookTitle).toBe('Atomic Habits')
    expect(state.items[0].id).toMatch(/^local-/)
  })

  it('deletes a note', async () => {
    const store = createStore()
    await store.dispatch(
      createNote({ bookId: 'b1', bookTitle: 'B', title: 'T', content: 'C', tags: [] }) as any
    )
    const noteId = (store.getState().notes as NotesSliceState).items[0].id

    await store.dispatch(deleteNote(noteId) as any)
    expect((store.getState().notes as NotesSliceState).items).toHaveLength(0)
  })

  it('selects notes by book', async () => {
    const store = createStore()
    await store.dispatch(
      createNote({ bookId: 'b1', bookTitle: 'B1', title: 'T', content: 'C', tags: [] }) as any
    )
    await store.dispatch(
      createNote({ bookId: 'b2', bookTitle: 'B2', title: 'T', content: 'C', tags: [] }) as any
    )
    const state = store.getState()
    expect(selectNotesByBook(state, 'b1')).toHaveLength(1)
    expect(selectNotesByBook(state, 'b2')).toHaveLength(1)
  })
})
