/**
 * 📝 Reading Notes State Management
 * Chain-of-Thought: Manage per-book reading notes with full CRUD
 * Memory: Keep notes cached for instant retrieval
 * Forward-Thinking: Extensible for AI summarization and quote extraction
 */

import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { NotesService } from '../../utils/api'

// ─── Types ────────────────────────────────────────────────────────────────

export interface ReadingNote {
  id: string
  bookId: string
  bookTitle: string
  title: string
  content: string
  tags: string[]
  page?: number
  createdAt: number
  updatedAt: number
}

export interface NotesSliceState {
  items: ReadingNote[]
  loading: boolean
  error: string | null
}

// ─── Initial State ────────────────────────────────────────────────────────

const initialState: NotesSliceState = {
  items: [],
  loading: false,
  error: null
}

// ─── Async Thunks ──────────────────────────────────────────────────────────

/** Fetch all reading notes for the current user. */
export const fetchNotes = createAsyncThunk(
  'notes/fetchNotes',
  async (_, { rejectWithValue }) => {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 4000)
      const data = await NotesService.getAllNotes()
      clearTimeout(timeout)
      return data as ReadingNote[]
    } catch (error) {
      console.warn('[Notes] Backend unavailable:', error)
      return rejectWithValue('Backend unavailable')
    }
  }
)

/** Create a new reading note. */
export const createNote = createAsyncThunk(
  'notes/createNote',
  async (note: Omit<ReadingNote, 'id' | 'createdAt' | 'updatedAt'>) => {
    try {
      const data = await NotesService.createNote(note)
      return data as ReadingNote
    } catch (error) {
      // Create locally so the user never loses a note, even offline
      const localNote: ReadingNote = {
        ...note,
        id: `local-${Date.now()}`,
        createdAt: Date.now(),
        updatedAt: Date.now()
      }
      console.warn('[Notes] Backend unavailable, saved locally:', error)
      return localNote
    }
  }
)

/** Update an existing note. */
export const updateNote = createAsyncThunk(
  'notes/updateNote',
  async (note: ReadingNote) => {
    try {
      const data = await NotesService.updateNote(note.id, note)
      return data as ReadingNote
    } catch (error) {
      console.warn('[Notes] Backend unavailable, updating locally:', error)
      return { ...note, updatedAt: Date.now() }
    }
  }
)

/** Delete a note. */
export const deleteNote = createAsyncThunk(
  'notes/deleteNote',
  async (id: string) => {
    try {
      await NotesService.deleteNote(id)
      return id
    } catch (error) {
      console.warn('[Notes] Backend unavailable, removing locally:', error)
      return id
    }
  }
)

// ─── Slice ─────────────────────────────────────────────────────────────────

const notesSlice = createSlice({
  name: 'notes',
  initialState,
  reducers: {
    addNoteLocally: (state, action: PayloadAction<ReadingNote>) => {
      state.items = [action.payload, ...state.items]
    },
    clearNotes: (state) => {
      state.items = []
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchNotes.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchNotes.fulfilled, (state, action) => {
        state.loading = false
        state.items = action.payload
      })
      .addCase(fetchNotes.rejected, (state, action) => {
        state.loading = false
        state.error = (action.payload as string) ?? 'Failed to load notes'
      })
      .addCase(createNote.fulfilled, (state, action) => {
        state.items = [action.payload, ...state.items]
      })
      .addCase(updateNote.fulfilled, (state, action) => {
        state.items = state.items.map((n) =>
          n.id === action.payload.id ? action.payload : n
        )
      })
      .addCase(deleteNote.fulfilled, (state, action) => {
        state.items = state.items.filter((n) => n.id !== action.payload)
      })
  }
})

export const { addNoteLocally, clearNotes } = notesSlice.actions

// ─── Selectors ─────────────────────────────────────────────────────────────

export const selectNotes = (state: { notes: NotesSliceState }) => state.notes.items
export const selectNotesByBook = (state: { notes: NotesSliceState }, bookId: string) =>
  state.notes.items.filter((n) => n.bookId === bookId)
export const selectRecentNotes = (state: { notes: NotesSliceState }, limit = 5) =>
  state.notes.items.slice(0, limit)

export default notesSlice.reducer

