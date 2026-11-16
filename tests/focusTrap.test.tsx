/**
 * ⌨️ Focus-trap regression tests
 *
 * `aria-modal="true"` is a promise. These tests hold the overlays to it:
 *   - Tab must cycle inside the dialog, never escape into the page behind it.
 *   - Shift+Tab from the first control must wrap to the last.
 *   - Closing must return focus to the control that opened the dialog.
 *
 * Without this, a keyboard reader on the onboarding gate could tab into the
 * dashboard rendered underneath (invisible, but fully interactive).
 */

import { act, fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'
import { useFocusTrap } from '../src/hooks/useFocusTrap'

const Dialog = ({ onCloseEvent }: { onCloseEvent?: () => void }) => {
    const [open, setOpen] = useState(true)
    const ref = useFocusTrap<HTMLDivElement>(open, () => {
        setOpen(false)
        onCloseEvent?.()
    })
    if (!open) return null
    return (
        <div ref={ref} role="dialog" aria-modal="true" aria-label="Trap test">
            <button type="button">first</button>
            <button type="button">middle</button>
            <button type="button">last</button>
        </div>
    )
}

describe('useFocusTrap', () => {
    it('moves focus into the dialog on open', () => {
        render(<Dialog />)
        expect(document.activeElement?.textContent).toBe('first')
    })

    it('wraps Tab from the last control back to the first', () => {
        render(<Dialog />)
        const last = screen.getByText('last')
        act(() => last.focus())

        fireEvent.keyDown(document, { key: 'Tab' })

        expect(document.activeElement?.textContent).toBe('first')
    })

    it('wraps Shift+Tab from the first control to the last', () => {
        render(<Dialog />)
        const first = screen.getByText('first')
        act(() => first.focus())

        fireEvent.keyDown(document, { key: 'Tab', shiftKey: true })

        expect(document.activeElement?.textContent).toBe('last')
    })

    it('pulls focus back if it somehow escaped the dialog', () => {
        render(<Dialog />)
        const outside = document.createElement('button')
        outside.textContent = 'outside'
        document.body.appendChild(outside)
        act(() => outside.focus())

        fireEvent.keyDown(document, { key: 'Tab' })

        expect(document.activeElement?.textContent).toBe('first')
        outside.remove()
    })

    it('closes on Escape and restores focus to the opener', () => {
        const opener = document.createElement('button')
        opener.textContent = 'opener'
        document.body.appendChild(opener)
        act(() => opener.focus())

        let escaped = false
        render(<Dialog onCloseEvent={() => { escaped = true }} />)
        // Focus moved inside…
        expect(document.activeElement?.textContent).toBe('first')

        fireEvent.keyDown(document, { key: 'Escape' })

        expect(escaped).toBe(true)
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
        expect(document.activeElement).toBe(opener)
        opener.remove()
    })
})
