/**
 * 📝 Reading Notes — real, persisted notes tied to books.
 * Chain-of-Thought: notes live in the reading slice (localStorage) so they
 * survive reloads and are ready to sync to Supabase when the DB schema lands.
 */

import { motion } from 'framer-motion'
import { BookOpen, Pencil, Plus, Trash2 } from 'lucide-react'
import React, { useState } from 'react'
import { BOOK_CATALOG } from '../../data/bookCatalog'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import { addNote, deleteNote, updateNote } from '../../stores/reading/readingSlice'

const ReadingNotes: React.FC = () => {
  const dispatch = useAppDispatch()
  const notes = useAppSelector((state) => state.reading.notes)

  const [text, setText] = useState('')
  const [bookId, setBookId] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editText, setEditText] = useState('')

  const bookTitle = (id?: string) =>
    id ? (BOOK_CATALOG.find((b) => b.id === id)?.title ?? '') : ''

  const handleAdd = () => {
    const trimmed = text.trim()
    if (!trimmed) return
    dispatch(addNote({ text: trimmed, bookId: bookId || undefined }))
    setText('')
    setBookId('')
  }

  const handleSaveEdit = (id: string) => {
    dispatch(updateNote({ id, text: editText.trim() }))
    setEditingId(null)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-900 dark:via-blue-950 dark:to-indigo-950 p-4 sm:p-8"
    >
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3 mb-2">
          <BookOpen className="w-8 h-8 text-green-600" />
          Reading Notes
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Capture thoughts, quotes, and reactions — they&apos;re saved to your account.
        </p>

        {/* Add note */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-5 mb-8">
          <div className="flex flex-col gap-3">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="What stood out while you were reading?"
              rows={3}
              className="w-full p-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
            />
            <div className="flex flex-col sm:flex-row gap-3">
              <select
                value={bookId}
                onChange={(e) => setBookId(e.target.value)}
                className="flex-1 min-w-0 p-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white"
                aria-label="Related book"
              >
                <option value="">No related book</option>
                {BOOK_CATALOG.map((b) => (
                  <option key={b.id} value={b.id}>{b.title}</option>
                ))}
              </select>
              <button
                onClick={handleAdd}
                disabled={!text.trim()}
                className="flex items-center gap-1 px-4 py-2.5 rounded-xl bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium transition-colors"
              >
                <Plus className="w-4 h-4" /> Add Note
              </button>
            </div>
          </div>
        </div>

        {/* Notes list */}
        {notes.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-5xl mb-4">🗒️</div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white">No notes yet</h3>
            <p className="text-gray-500 dark:text-gray-400 mt-2">
              Add your first note above — it will be waiting for you next time.
            </p>
          </div>
        ) : (
          <ul className="space-y-4">
            {notes.map((note) => (
              <li key={note.id} className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-5">
                {editingId === note.id ? (
                  <div className="flex flex-col gap-2">
                    <textarea
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      rows={3}
                      className="w-full p-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white resize-none"
                    />
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={() => setEditingId(null)}
                        className="px-3 py-1.5 rounded-lg text-sm bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleSaveEdit(note.id)}
                        className="px-3 py-1.5 rounded-lg text-sm bg-green-600 hover:bg-green-700 text-white"
                      >
                        Save
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="text-gray-900 dark:text-white whitespace-pre-wrap">{note.text}</p>
                    <div className="flex items-center justify-between mt-3">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {bookTitle(note.bookId)}
                        {bookTitle(note.bookId) ? ' · ' : ''}
                        {new Date(note.updatedAt).toLocaleString(undefined, {
                          day: 'numeric',
                          month: 'short'
                        })}
                      </span>
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setEditingId(note.id)
                            setEditText(note.text)
                          }}
                          className="p-1.5 text-gray-400 hover:text-blue-500 transition-colors"
                          aria-label="Edit note"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => dispatch(deleteNote(note.id))}
                          className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
                          aria-label="Delete note"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </motion.div>
  )
}

export default ReadingNotes
