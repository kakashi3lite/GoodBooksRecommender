/**
 * ⌘K Command Palette — actions first, search second.
 *
 * Chain-of-Thought:
 *   Premium web apps (Linear, Raycast, Vercel) treat ⌘K as a *do* surface,
 *   not a search box. This palette keeps the reader's hands on the keyboard
 *   for the three things they actually do: log progress, jump to a book, and
 *   ask the companion. Book results come from the same live edge API the
 *   Discover page uses (`/api/books/web-search`), so the palette can surface
 *   ANY book, not just the curated catalog.
 *
 *   Progressive disclosure: one input, no filters, no settings. Typing
 *   "dune" narrows to books; typing "log" surfaces the progress action;
 *   anything else becomes an "Ask the companion" command — the palette never
 *   dead-ends on "no results".
 *
 * Memory: nothing persists here by design. The palette is a transient surface;
 * conversation memory lives in the AI slice and reading data in the reading slice.
 *
 * Accessibility: role=dialog + aria-modal, a real listbox with aria-activedescendant,
 * arrow-key navigation, Enter to run, Escape to close, and focus restored to the
 * previously focused element on close. Body scroll is locked while open.
 */

import { AnimatePresence, motion } from 'framer-motion'
import {
  ArrowRight,
  BookOpen,
  CornerDownLeft,
  Heart,
  Home,
  MessageCircle,
  Moon,
  Newspaper,
  Search,
  Sparkles,
  Sun,
  TrendingUp,
  Users,
  Zap,
  type LucideIcon
} from 'lucide-react'
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import { addMessage, openAssistant, sendMessage } from '../../stores/ai/aiSlice'
import { setTheme } from '../../stores/dashboard/dashboardSlice'
import { logReadingSession } from '../../stores/reading/readingSlice'
import { API_ENDPOINTS } from '../../utils/api'
import { computePace } from '../../utils/readingInsights'

interface PaletteBook {
  id: string
  title: string
  authors: string
  cover_url?: string
}

interface Command {
  id: string
  group: string
  label: string
  hint?: string
  icon: LucideIcon
  keywords?: string
  run: () => void
}

/** Subsequence match so "lgr" finds "Log reading session" (Raycast-style). */
const fuzzyMatch = (label: string, query: string): boolean => {
  const q = query.toLowerCase().replace(/\s+/g, '')
  if (!q) return true
  const target = label.toLowerCase()
  let cursor = 0
  for (const char of q) {
    cursor = target.indexOf(char, cursor)
    if (cursor === -1) return false
    cursor += 1
  }
  return true
}

const CommandPalette: React.FC = () => {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()

  const theme = useAppSelector((state) => state.dashboard.theme)
  const readingEntries = useAppSelector((state) => state.reading.currentlyReading)
  const readingLog = useAppSelector((state) => state.reading.readingLog)
  const recommendations = useAppSelector((state) => state.books.recommendations)

  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const [books, setBooks] = useState<PaletteBook[]>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const restoreFocusRef = useRef<HTMLElement | null>(null)
  const debounceRef = useRef<number | undefined>(undefined)

  const { avgPagesPerSession } = useMemo(() => computePace(readingLog), [readingLog])

  const activeEntry = useMemo(
    () => readingEntries.find((e) => e.finishedAt === null),
    [readingEntries]
  )
  const activeTitle = useMemo(() => {
    if (!activeEntry) return null
    return (
      recommendations.find((b) => b.id === activeEntry.bookId)?.title ??
      activeEntry.book?.title ??
      null
    )
  }, [activeEntry, recommendations])

  const close = useCallback(() => {
    setOpen(false)
    setQuery('')
    setActiveIndex(0)
    setBooks([])
    // Return focus to whatever the reader was using (keyboard users are not lost).
    restoreFocusRef.current?.focus?.()
  }, [])

  const askCompanion = useCallback(
    (message: string) => {
      const text = message.trim() || 'What should I read next?'
      dispatch(openAssistant())
      dispatch(
        addMessage({
          id: `user-${Date.now()}`,
          role: 'user',
          content: text,
          timestamp: Date.now()
        })
      )
      dispatch(sendMessage(text))
    },
    [dispatch]
  )

  // ─── Commands ────────────────────────────────────────────────────────────
  const commands = useMemo<Command[]>(() => {
    const go: Command[] = [
      { id: 'go-dashboard', group: 'Go to', label: 'Dashboard', icon: Home, run: () => navigate('/') },
      { id: 'go-discover', group: 'Go to', label: 'Discover books', icon: Search, run: () => navigate('/discover') },
      { id: 'go-reading', group: 'Go to', label: 'Currently Reading', icon: BookOpen, run: () => navigate('/reading') },
      { id: 'go-wishlist', group: 'Go to', label: 'Wishlist', icon: Heart, run: () => navigate('/wishlist') },
      { id: 'go-analytics', group: 'Go to', label: 'Reading Analytics', icon: TrendingUp, run: () => navigate('/analytics') },
      { id: 'go-news', group: 'Go to', label: 'Book News', icon: Newspaper, run: () => navigate('/news') },
      { id: 'go-community', group: 'Go to', label: 'Community', icon: Users, run: () => navigate('/community') }
    ]

    const actions: Command[] = []
    if (activeEntry) {
      const label = activeTitle ? `Log ${avgPagesPerSession} pages — ${activeTitle}` : `Log ${avgPagesPerSession} pages`
      actions.push({
        id: 'log-progress',
        group: 'Actions',
        label,
        hint: 'Your usual session',
        icon: Zap,
        keywords: 'progress session read pages',
        run: () => {
          dispatch(logReadingSession({ bookId: activeEntry.bookId, pages: avgPagesPerSession }))
        }
      })
    }
    actions.push({
      id: 'toggle-theme',
      group: 'Actions',
      label: theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode',
      icon: theme === 'dark' ? Sun : Moon,
      keywords: 'theme appearance dark light',
      run: () => dispatch(setTheme(theme === 'dark' ? 'light' : 'dark'))
    })
    actions.push({
      id: 'ask-open',
      group: 'Actions',
      label: 'Ask the reading companion',
      hint: '⌘J',
      icon: MessageCircle,
      keywords: 'ai chat recommend assistant',
      run: () => dispatch(openAssistant())
    })

    return [...actions, ...go]
  }, [activeEntry, activeTitle, avgPagesPerSession, dispatch, navigate, theme])

  const filteredCommands = useMemo(() => {
    if (!query.trim()) return commands
    return commands.filter(
      (c) => fuzzyMatch(c.label, query) || (c.keywords ? fuzzyMatch(c.keywords, query) : false)
    )
  }, [commands, query])

  const bookCommands = useMemo<Command[]>(
    () =>
      books.map((book) => ({
        id: `book-${book.id}`,
        group: 'Books',
        label: book.title,
        hint: book.authors,
        icon: BookOpen,
        run: () => navigate(`/book/${encodeURIComponent(book.id)}`)
      })),
    [books, navigate]
  )

  const askCommand = useMemo<Command[]>(() => {
    const q = query.trim()
    if (!q) return []
    return [
      {
        id: 'ask-query',
        group: 'Ask',
        label: `Ask the companion: “${q}”`,
        hint: 'AI picks with reasons',
        icon: Sparkles,
        run: () => askCompanion(q)
      }
    ]
  }, [askCompanion, query])

  const results = useMemo(
    () => [...filteredCommands, ...bookCommands, ...askCommand],
    [askCommand, bookCommands, filteredCommands]
  )

  /** Safe lookup (avoids dynamic property access on an index sink). */
  const activeCommand = useMemo(
    () => results.find((_, index) => index === activeIndex),
    [activeIndex, results]
  )

  // ─── Keyboard ────────────────────────────────────────────────────────────
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const isPaletteShortcut =
        (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k'
      if (isPaletteShortcut) {
        event.preventDefault()
        setOpen((prev) => {
          if (!prev) restoreFocusRef.current = document.activeElement as HTMLElement | null
          return !prev
        })
        return
      }
      if (!open) return

      if (event.key === 'Escape') {
        event.preventDefault()
        close()
      } else if (event.key === 'ArrowDown') {
        event.preventDefault()
        setActiveIndex((i) => (results.length === 0 ? 0 : (i + 1) % results.length))
      } else if (event.key === 'ArrowUp') {
        event.preventDefault()
        setActiveIndex((i) => (results.length === 0 ? 0 : (i - 1 + results.length) % results.length))
      } else if (event.key === 'Enter') {
        const command = results.find((_, index) => index === activeIndex)
        if (command) {
          event.preventDefault()
          close()
          command.run()
        }
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [activeIndex, close, open, results])

  // Focus the input + lock background scroll while open.
  useEffect(() => {
    if (!open) return
    inputRef.current?.focus()
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previousOverflow
    }
  }, [open])

  // Reset the highlight whenever the result set changes shape.
  useEffect(() => {
    setActiveIndex(0)
  }, [query])

  // ─── Live book search (debounced, same edge API as Discover) ─────────────
  useEffect(() => {
    if (!open) return
    const q = query.trim()
    window.clearTimeout(debounceRef.current)
    if (q.length < 2) {
      setBooks([])
      return
    }
    debounceRef.current = window.setTimeout(async () => {
      try {
        const res = await fetch(
          `${API_ENDPOINTS.books.webSearch()}?q=${encodeURIComponent(q)}&limit=5`
        )
        const data = (await res.json()) as { data?: PaletteBook[] }
        setBooks((data.data ?? []).slice(0, 5))
      } catch {
        setBooks([])
      }
    }, 300)
    return () => window.clearTimeout(debounceRef.current)
  }, [open, query])

  // Keep the active row visible when arrowing through a long list.
  useEffect(() => {
    const node = listRef.current?.querySelector<HTMLElement>(`[data-index="${activeIndex}"]`)
    node?.scrollIntoView({ block: 'nearest' })
  }, [activeIndex])

  // Group headers are rendered once per contiguous group.
  let lastGroup = ''

  return (
    <AnimatePresence>
      {open && (
        <div className="palette-backdrop" onMouseDown={close}>
          <div
            className="flex min-h-full items-start justify-center p-4 pt-[12vh]"
            role="presentation"
          >
            <motion.div
              className="palette-panel"
              role="dialog"
              aria-modal="true"
              aria-label="Command palette"
              initial={{ opacity: 0, y: -12, scale: 0.985 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.99 }}
              transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
              onMouseDown={(event) => event.stopPropagation()}
            >
              {/* Search row */}
              <div className="flex items-center gap-3 border-b border-[var(--hairline)] px-4 py-3.5">
                <Search className="h-4 w-4 shrink-0 text-[var(--text-tertiary)]" />
                <input
                  ref={inputRef}
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Log progress, jump to a book, or ask anything…"
                  aria-label="Search commands and books"
                  aria-controls="palette-results"
                  aria-activedescendant={activeCommand ? `palette-item-${activeCommand.id}` : undefined}
                  className="w-full bg-transparent text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] outline-none"
                  autoComplete="off"
                  spellCheck={false}
                />
                <span className="palette-kbd">esc</span>
              </div>

              {/* Results */}
              <div
                ref={listRef}
                id="palette-results"
                role="listbox"
                aria-label="Commands"
                className="max-h-[24rem] overflow-y-auto p-2"
              >
                {results.length === 0 && (
                  <p className="px-3 py-8 text-center text-sm text-[var(--text-tertiary)]">
                    Nothing matched. Try a book title, or ask the companion.
                  </p>
                )}

                {results.map((command, index) => {
                  const showGroup = command.group !== lastGroup
                  lastGroup = command.group
                  const Icon = command.icon
                  return (
                    <React.Fragment key={command.id}>
                      {showGroup && (
                        <p className="type-eyebrow px-3 pb-1 pt-3 first:pt-1">{command.group}</p>
                      )}
                      <button
                        type="button"
                        id={`palette-item-${command.id}`}
                        role="option"
                        aria-selected={index === activeIndex}
                        data-active={index === activeIndex}
                        data-index={index}
                        className="palette-row"
                        onMouseMove={() => setActiveIndex(index)}
                        onClick={() => {
                          close()
                          command.run()
                        }}
                      >
                        <Icon className="h-4 w-4 shrink-0" />
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-sm">{command.label}</span>
                          {command.hint && (
                            <span className="block truncate text-xs text-[var(--text-tertiary)]">
                              {command.hint}
                            </span>
                          )}
                        </span>
                        {index === activeIndex && (
                          <CornerDownLeft className="h-3.5 w-3.5 shrink-0 text-[var(--text-tertiary)]" />
                        )}
                      </button>
                    </React.Fragment>
                  )
                })}
              </div>

              {/* Footer hints */}
              <div className="flex items-center justify-between border-t border-[var(--hairline)] px-4 py-2 text-[11px] text-[var(--text-tertiary)]">
                <span className="flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <span className="palette-kbd">↑</span>
                    <span className="palette-kbd">↓</span>
                    move
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="palette-kbd">↵</span>
                    open
                  </span>
                </span>
                <span className="flex items-center gap-1">
                  Reading companion
                  <ArrowRight className="h-3 w-3" />
                  <span className="palette-kbd">⌘J</span>
                </span>
              </div>
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>
  )
}

export default CommandPalette
