/**
 * 🎚️ Reading pace — one definition, three surfaces
 *
 * Chain-of-Thought: onboarding asked "how do you like to read?", stored the answer
 * as `preferredMoods`, and nothing else in the app could read or change it. The
 * pace list lived inside the onboarding component, so Settings could not offer the
 * same question and a reader could never revise an answer they gave once.
 *
 * This module is the single source of truth: onboarding writes it, Settings
 * rewrites it, `buildProfile` consumes the moods it produces.
 */

export type ReadingPaceId = 'quick' | 'mixed' | 'epic'

export interface ReadingPaceOption {
    id: ReadingPaceId
    label: string
    blurb: string
    moods: string[]
}

export const READING_PACE: ReadingPaceOption[] = [
    { id: 'quick', label: 'Quick reads', blurb: 'shorter, punchy books', moods: ['fast-paced'] },
    { id: 'mixed', label: 'A bit of both', blurb: 'varied lengths & pace', moods: [] },
    { id: 'epic', label: 'Epic tomes', blurb: 'sink into big worlds', moods: ['epic'] }
]

/** Moods to store when a reader picks a pace. */
export const moodsForPace = (id: string): string[] =>
    READING_PACE.find((option) => option.id === id)?.moods ?? []

/**
 * Reverse mapping, so Settings can highlight the reader's current answer.
 * A stored mood set that matches no option means "no stated preference" — the
 * neutral `mixed` pace — rather than silently claiming a preference.
 */
export const paceForMoods = (moods: string[] | undefined): ReadingPaceId => {
    const stored = new Set(moods ?? [])
    const match = READING_PACE.find(
        (option) => option.moods.length > 0 && option.moods.every((mood) => stored.has(mood))
    )
    return match?.id ?? 'mixed'
}
