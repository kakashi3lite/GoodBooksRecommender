/**
 * ⌨️ useFocusTrap — make `aria-modal` true.
 *
 * Chain-of-Thought (accessibility):
 *   Five overlays (onboarding, ⌘K palette, add-book, settings, completion) all
 *   declare `role="dialog" aria-modal="true"`. None of them trapped focus, so
 *   the claim was false: pressing Tab on the first screen in the product moved
 *   focus into the dashboard rendered *behind* the overlay — invisible to the
 *   reader, fully interactive for a keyboard or switch user. A false
 *   `aria-modal` is worse than none: assistive tech is told to ignore the page
 *   while the browser still exposes it.
 *
 *   This hook does the four things a modal must do:
 *     1. Move focus inside when it opens (to the first focusable control).
 *     2. Keep Tab / Shift+Tab cycling within the container.
 *     3. Restore focus to whatever the reader was using when it closes.
 *     4. Optionally close on Escape.
 *
 *   Visibility is evaluated at keypress time (not cached on open) because the
 *   panels change content while open — steps, results, validation states.
 */

import { useEffect, useRef } from 'react'

const FOCUSABLE = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled]):not([type="hidden"])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
].join(',')

/**
 * Is this element actually reachable by the keyboard?
 *
 * Chain-of-Thought: the obvious test (`offsetWidth > 0`) is wrong twice over.
 * It reads layout (jsdom reports 0 for everything, so the trap silently
 * became a no-op under test), and it misses ancestors hidden by CSS. We use
 * `checkVisibility()` where the platform provides it and otherwise accept the
 * element — the selector has already excluded disabled/hidden controls.
 */
const isReachable = (el: HTMLElement): boolean => {
    if (el.hasAttribute('hidden') || el.getAttribute('aria-hidden') === 'true') return false
    const check = (el as HTMLElement & { checkVisibility?: (opts?: object) => boolean })
        .checkVisibility
    if (typeof check !== 'function') return true
    try {
        return check.call(el, { checkVisibilityCSS: true, contentVisibilityAuto: true })
    } catch {
        return true
    }
}

const visibleFocusables = (container: HTMLElement): HTMLElement[] =>
    Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(isReachable)

/**
 * Trap keyboard focus inside the element returned by this ref while `active`.
 *
 * @param active     whether the overlay is currently open
 * @param onEscape   optional Escape handler
 * @returns ref to attach to the dialog element
 */
export const useFocusTrap = <T extends HTMLElement = HTMLDivElement>(
    active: boolean,
    onEscape?: () => void
) => {
    const containerRef = useRef<T | null>(null)
    const escapeRef = useRef(onEscape)
    escapeRef.current = onEscape

    useEffect(() => {
        if (!active) return
        const container = containerRef.current
        if (!container) return

        const previouslyFocused = document.activeElement as HTMLElement | null

        // 1. Move focus inside. If the overlay already focused a control
        //    (the palette focuses its input), leave that alone.
        if (!container.contains(document.activeElement)) {
            visibleFocusables(container)[0]?.focus()
        }

        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape' && escapeRef.current) {
                event.preventDefault()
                escapeRef.current()
                return
            }
            if (event.key !== 'Tab') return

            const items = visibleFocusables(container)
            if (items.length === 0) return

            const first = items[0]
            const last = items[items.length - 1]
            const activeEl = document.activeElement as HTMLElement | null

            // 2. Cycle. Also pull focus back if it somehow escaped the dialog.
            if (!activeEl || !container.contains(activeEl)) {
                event.preventDefault()
                first.focus()
                return
            }
            if (event.shiftKey && activeEl === first) {
                event.preventDefault()
                last.focus()
            } else if (!event.shiftKey && activeEl === last) {
                event.preventDefault()
                first.focus()
            }
        }

        document.addEventListener('keydown', onKeyDown)
        return () => {
            document.removeEventListener('keydown', onKeyDown)
            // 3. Give focus back so the reader continues where they were.
            previouslyFocused?.focus?.()
        }
    }, [active])

    return containerRef
}
