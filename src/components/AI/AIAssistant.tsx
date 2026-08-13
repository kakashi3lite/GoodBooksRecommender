/**
 * 🤖 AI Assistant — Conversational Reading Companion
 * Chain-of-Thought: Floating chat panel that recommends books conversationally
 * Memory: Chat history lives in the Redux `ai` slice
 * Forward-Thinking: Quick-action chips for common discovery intents
 */

import { AnimatePresence, motion } from 'framer-motion'
import { Bot, RefreshCw, Send, Sparkles, X } from 'lucide-react'
import React, { useEffect, useRef, useState } from 'react'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import type { ChatMessage } from '../../stores/ai/aiSlice'
import {
  addMessage,
  clearConversation,
  requestFreshPicks,
  sendMessage,
  toggleAssistant
} from '../../stores/ai/aiSlice'
import BookCover from '../UI/BookCover'

// Quick actions shown as suggestion chips
const QUICK_ACTIONS = [
  'Recommend me a book',
  'Something for a cozy mood',
  'Similar to my last thriller'
]

/**
 * Renders a single chat message bubble with optional book suggestion cards.
 * Suggestions now carry a personalization `reason` ("why this book") so the
 * reader sees the connection to their taste instead of a bare title list.
 */
const MessageBubble: React.FC<{ message: ChatMessage }> = ({ message }) => {
  const isUser = message.role === 'user'
  const dispatch = useAppDispatch()
  const isStreaming = useAppSelector((state) => state.ai.isStreaming)
  const suggestions = message.bookSuggestions

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}
    >
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-lg ${isUser
          ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-br-sm'
          : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-bl-sm border border-gray-200 dark:border-gray-700'
          }`}
      >
        <p className="leading-relaxed whitespace-pre-wrap">{message.content}</p>

        {suggestions && suggestions.length > 0 && (
          <div className="mt-3 space-y-2">
            {suggestions.map((book) => (
              <div
                key={book.id}
                className="flex items-start gap-3 rounded-xl bg-gray-50 dark:bg-gray-700/60 p-2.5 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
              >
                <BookCover
                  title={book.title}
                  author={book.authors}
                  size="xs"
                  rounded="sm"
                  showText={false}
                />
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-sm truncate">{book.title}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {book.authors}
                  </p>
                  {book.reason && (
                    <p className="text-[11px] text-purple-600 dark:text-purple-300 mt-0.5 leading-snug">
                      {book.reason}
                    </p>
                  )}
                  {book.rating !== undefined && (
                    <p className="text-xs text-yellow-500 mt-0.5">
                      ★ {book.rating.toFixed(1)}
                    </p>
                  )}
                </div>
                <Sparkles className="w-4 h-4 text-purple-500 flex-shrink-0 mt-0.5" />
              </div>
            ))}
            {!isStreaming && (
              <button
                onClick={() => dispatch(requestFreshPicks())}
                className="w-full flex items-center justify-center gap-1.5 text-xs py-2 rounded-lg bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 hover:bg-purple-100 dark:hover:bg-purple-900/50 transition-colors"
                aria-label="Get different book picks"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Different picks
              </button>
            )}
          </div>
        )}
      </div>
    </motion.div>
  )
}

/**
 * AI Assistant — floating chat panel.
 * Keyboard shortcut: Cmd+K (or Ctrl+K) toggles the panel.
 */
const AIAssistant: React.FC = () => {
  const dispatch = useAppDispatch()
  const isOpen = useAppSelector((state) => state.ai.isOpen)
  const isStreaming = useAppSelector((state) => state.ai.isStreaming)
  const messages = useAppSelector((state) => state.ai.messages)

  const [input, setInput] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to the latest message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isOpen])

  // Keyboard shortcut: Cmd+K / Ctrl+K toggles the assistant
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        dispatch(toggleAssistant())
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [dispatch])

  const handleSend = (text?: string) => {
    const content = (text ?? input).trim()
    if (!content || isStreaming) return

    dispatch(
      addMessage({
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        timestamp: Date.now()
      })
    )
    dispatch(sendMessage(content))
    setInput('')
  }

  return (
    <>
      {/* Floating toggle button */}
      <motion.button
        onClick={() => dispatch(toggleAssistant())}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 text-white shadow-2xl shadow-blue-500/30 flex items-center justify-center hover:scale-105 active:scale-95 transition-transform"
        whileHover={{ y: -3 }}
        whileTap={{ scale: 0.95 }}
        aria-label="Toggle AI Assistant"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Bot className="w-6 h-6" />}
        {!isOpen && (
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full border-2 border-white dark:border-gray-900 animate-pulse" />
        )}
      </motion.button>

      {/* Chat panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 40, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 40, scale: 0.96 }}
            transition={{ type: 'spring', stiffness: 300, damping: 28 }}
            className="fixed bottom-24 right-6 z-50 w-[380px] max-w-[calc(100vw-3rem)] h-[520px] max-h-[70vh] rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-2xl flex flex-col overflow-hidden"
            role="dialog"
            aria-label="AI Reading Assistant"
          >
            {/* Header */}
            <div className="px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5" />
                <div>
                  <h3 className="font-semibold text-sm leading-tight">AI Reading Companion</h3>
                  <p className="text-[11px] text-blue-100">Personalized to your reading</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => dispatch(clearConversation())}
                  className="p-1.5 rounded-lg hover:bg-white/20 transition-colors"
                  aria-label="Clear conversation"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 bg-gray-50 dark:bg-gray-950/50">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center text-gray-500 dark:text-gray-400">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900/40 dark:to-purple-900/40 flex items-center justify-center mb-4">
                    <Sparkles className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                  </div>
                  <h4 className="font-semibold text-gray-700 dark:text-gray-200 mb-1">
                    How can I help you read better?
                  </h4>
                  <p className="text-xs max-w-[220px]">
                    Ask for recommendations, mood matches, or something similar to a favorite
                    book.
                  </p>
                </div>
              ) : (
                messages.map((message) => (
                  <MessageBubble key={message.id} message={message} />
                ))
              )}

              {/* Typing indicator */}
              {isStreaming && (
                <div className="flex justify-start mb-3">
                  <div className="bg-white dark:bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-3 border border-gray-200 dark:border-gray-700 shadow">
                    <div className="flex gap-1">
                      {[0, 1, 2].map((i) => (
                        <span
                          key={i}
                          className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-bounce"
                          style={{ animationDelay: `${i * 0.15}s` }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Quick actions */}
            {messages.length === 0 && (
              <div className="px-4 pb-2 flex flex-wrap gap-2">
                {QUICK_ACTIONS.map((action) => (
                  <button
                    key={action}
                    onClick={() => handleSend(action)}
                    className="text-xs px-3 py-1.5 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors"
                  >
                    {action}
                  </button>
                ))}
              </div>
            )}

            {/* Input */}
            <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSend()
                  }}
                  placeholder="Ask about books..."
                  className="flex-1 px-4 py-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 border border-transparent focus:border-blue-500 focus:bg-white dark:focus:bg-gray-800 outline-none text-sm transition-colors"
                  aria-label="Message the AI assistant"
                />
                <motion.button
                  onClick={() => handleSend()}
                  whileTap={{ scale: 0.9 }}
                  disabled={!input.trim() || isStreaming}
                  className="p-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
                  aria-label="Send message"
                >
                  <Send className="w-4 h-4" />
                </motion.button>
              </div>
              <p className="text-[10px] text-gray-400 mt-1.5 text-center">
                Press <kbd className="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">⌘K</kbd> to
                toggle
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

export default AIAssistant
