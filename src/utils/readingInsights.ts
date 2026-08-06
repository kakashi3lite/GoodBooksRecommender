/**
 * 🧠 Reading Insights — the psychology layer.
 * Chain-of-Thought: motivation comes from honest, personal numbers, not
 * fake ones. This module derives a reader's real pace (average pages per
 * session from their actual log), estimates time-to-finish for open books
 * (goal-gradient + Zeigarnik pull), and labels their reading persona
 * (identity-based habit building). All inputs are the user's own data.
 */

import type { ReadingLogEntry } from '../stores/reading/readingSlice'

export interface PaceInfo {
    avgPagesPerSession: number
    sessionsToday: number
    pagesToday: number
    loggedToday: boolean
}

/** Today's local YYYY-MM-DD key (same format the reading slice stores). */
export const todayKey = (): string => {
    const d = new Date()
    const m = `${d.getMonth() + 1}`.padStart(2, '0')
    const day = `${d.getDate()}`.padStart(2, '0')
    return `${d.getFullYear()}-${m}-${day}`
}

/**
 * Real pace from the reader's own log. Falls back to a sensible 30
 * pages/session when there is no history yet (never a hardcoded "+20").
 */
export const computePace = (log: ReadingLogEntry[]): PaceInfo => {
    const totalPages = log.reduce((a, l) => a + l.pages, 0)
    const avgPagesPerSession = log.length > 0 ? Math.max(10, Math.round(totalPages / log.length)) : 30
    const today = todayKey()
    const todayEntries = log.filter((l) => l.date === today)
    return {
        avgPagesPerSession,
        sessionsToday: todayEntries.length,
        pagesToday: todayEntries.reduce((a, l) => a + l.pages, 0),
        loggedToday: todayEntries.length > 0
    }
}

/** Rough hours remaining, from pages left at the reader's own pace. */
export const estimateHoursLeft = (
    pagesLeft: number,
    avgPagesPerSession: number,
    sessionMinutes = 30
): number => {
    if (pagesLeft <= 0) return 0
    const sessions = Math.ceil(pagesLeft / Math.max(1, avgPagesPerSession))
    return Math.max(1, Math.round((sessions * sessionMinutes) / 60))
}

/** Human label for the time estimate. */
export const formatHours = (hours: number): string =>
    hours < 1 ? '<1h' : hours <= 1 ? '~1h' : `~${hours}h`

/**
 * Identity label from real patterns — visible persona (identity-based habit
 * formation). Used by the Dashboard + completion ceremony.
 */
export const personaOf = (
    avgPagesPerSession: number,
    distinctDays: number,
    finishedCount: number
): string => {
    if (avgPagesPerSession >= 60) return 'Binge Reader'
    if (avgPagesPerSession >= 40) return 'Immersive Reader'
    if (distinctDays >= 5) return 'Consistent Reader'
    if (finishedCount >= 5) return 'Seasoned Reader'
    return 'Rising Reader'
}

export const personaEmoji = (persona: string): string => {
    switch (persona) {
        case 'Binge Reader': return '🔥'
        case 'Immersive Reader': return '🌊'
        case 'Consistent Reader': return '📅'
        case 'Seasoned Reader': return '🎖️'
        default: return '🌱'
    }
}

/** Distinct days with a logged session (for persona + analytics). */
export const distinctReadingDays = (log: ReadingLogEntry[]): number =>
    new Set(log.map((l) => l.date)).size
