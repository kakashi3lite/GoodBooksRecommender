/**
 * 🎨 Cover Art Engine Tests
 * Chain-of-Thought: Verify determinism, genre-aware hues, per-book variation,
 * monogram extraction, and valid CSS output.
 */

import { describe, expect, it } from 'vitest'
import {
    buildCoverBackground,
    buildDotPattern,
    getBookInitials,
    getCoverPalette,
    hashString
} from '../src/utils/coverArt'

describe('cover art engine', () => {
    it('hashes deterministically and distinguishes inputs', () => {
        expect(hashString('Dune')).toBe(hashString('Dune'))
        expect(hashString('Dune')).not.toBe(hashString('Dune 2'))
        expect(hashString('')).toBe(hashString(''))
    })

    it('produces the same palette for the same book (deterministic + cached)', () => {
        const a = getCoverPalette('Dune', ['Science Fiction', 'Fantasy'], 'b-11')
        const b = getCoverPalette('Dune', ['Science Fiction', 'Fantasy'], 'b-11')
        expect(a).toEqual(b)
        expect(a.from).toBe(b.from)
        expect(a.text).toBe(b.text)
    })

    it('varies palettes per book title (siblings don’t collide)', () => {
        const a = getCoverPalette('Dune', ['Science Fiction'])
        const b = getCoverPalette('Foundation', ['Science Fiction'])
        expect(a.from).not.toBe(b.from)
        expect(a.hue).not.toBe(b.hue)
    })

    it('maps genres to distinct base hues', () => {
        const sciFi = getCoverPalette('Hail Mary', ['Science Fiction'])
        const romance = getCoverPalette('Beach Read', ['Romance'])
        const horror = getCoverPalette('Dracula', ['Horror'])
        // Blue-ish vs rose-ish vs crimson — clearly separated
        expect(Math.abs(sciFi.hue - romance.hue)).toBeGreaterThan(80)
        expect(Math.abs(romance.hue - horror.hue)).toBeGreaterThan(10)
    })

    it('uses the same seed to disambiguate identical titles', () => {
        const a = getCoverPalette('Project', ['Fiction'], 'edition-1')
        const b = getCoverPalette('Project', ['Fiction'], 'edition-2')
        expect(a.from).not.toBe(b.from)
    })

    it('always emits a readable text color (either dark-on-light or light-on-dark)', () => {
        const darkish = getCoverPalette('The Silent Patient', ['Thriller'])
        // Text is either near-white or near-black — never mid-gray
        const isReadable = (c: string) => c === '#fafaf9' || c === '#1c1917'
        expect(isReadable(darkish.text)).toBe(true)
    })

    it('extracts two-letter monograms from titles', () => {
        expect(getBookInitials('Project Hail Mary')).toBe('PH')
        expect(getBookInitials('Dune')).toBe('D')
        expect(getBookInitials('')).toBe('B')
        expect(getBookInitials('The Midnight Library')).toBe('TM')
    })

    it('builds valid CSS strings for background and pattern', () => {
        const palette = getCoverPalette('Circe', ['Fantasy'])
        expect(buildCoverBackground(palette)).toContain('linear-gradient')
        expect(buildCoverBackground(palette)).toContain('hsl(')
        expect(buildDotPattern(palette)).toContain('radial-gradient')
    })
})
