/**
 * 🥇 useLatestRequest — only the newest async result may touch state.
 *
 * Chain-of-Thought:
 *   Discover and the ⌘K palette both fire a debounced fetch on every keystroke.
 *   Responses are not ordered: typing "dune" then "dunes" can resolve "dune"
 *   *after* "dunes" and overwrite the newer list with results for a query the
 *   reader has already moved past. To the reader it looks like search is
 *   broken — they type, and the list shows something they did not ask for.
 *
 *   The fix is a monotonically increasing request id (the classic
 *   "latest wins" guard) plus an AbortController so the stale request is
 *   actually cancelled rather than merely ignored. The hook returns `null`
 *   for superseded calls, so callers can skip their state update with a
 *   single `if (!result) return`.
 */

import { useCallback, useEffect, useRef } from 'react'

export interface LatestRequest {
    /**
     * Run `task` as the newest request. Resolves to `null` when a newer call
     * started in the meantime (the result must be ignored).
     */
    run: <T>(task: (signal: AbortSignal) => Promise<T>) => Promise<T | null>
    /** Abort the in-flight request and ignore its result (e.g. on unmount). */
    cancel: () => void
}

export const useLatestRequest = (): LatestRequest => {
    const sequence = useRef(0)
    const controller = useRef<AbortController | null>(null)

    const cancel = useCallback(() => {
        // Bumping the sequence is what makes the result stale; aborting is what
        // frees the request. Both are needed.
        sequence.current += 1
        controller.current?.abort()
        controller.current = null
    }, [])

    // Never let a late response call setState after unmount.
    useEffect(() => cancel, [cancel])

    const run = useCallback(
        async <T,>(task: (signal: AbortSignal) => Promise<T>): Promise<T | null> => {
            cancel()
            const id = sequence.current
            const current = new AbortController()
            controller.current = current

            let result: T
            try {
                result = await task(current.signal)
            } catch (error) {
                if (current.signal.aborted) return null
                throw error
            }

            return id === sequence.current ? result : null
        },
        [cancel]
    )

    return { run, cancel }
}
