/**
 * 🎨 Cover Art Engine — deterministic, offline, beautiful
 * Chain-of-Thought: Generate a stable, genre-aware gradient palette + typography
 * for every book so covers look intentional even with no image asset.
 *
 * Why this exists:
 *  - The catalog has no real cover images yet, and the app must work offline.
 *  - A deterministic hash → same book always gets the same palette (no flicker).
 *  - Genre drives the base hue (sci-fi → blue, romance → rose, fantasy → violet),
 *    the title hash adds a subtle per-book variation so siblings don't collide.
 *  - Text contrast is computed from the palette so covers stay readable in
 *    both light and dark themes.
 *
 * Forward-Thinking: when real cover URLs / Open Library ISBNs land, the
 * `<BookCover>` component overlays the real image on this generated base.
 */

export interface CoverPalette {
  /** gradient start color (css) */
  from: string
  /** gradient end color (css) */
  to: string
  /** darker accent used for the spine / edges */
  accent: string
  /** primary text color — contrast-computed */
  text: string
  /** secondary text color (muted, alpha) */
  muted: string
  /** base hue (for debugging / extension) */
  hue: number
}

// ─── Deterministic hashing (FNV-1a) ───────────────────────────────────────

export const hashString = (input: string): number => {
  let h = 0x811c9dc5 // FNV-1a offset basis
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i)
    h = Math.imul(h, 0x01000193) // FNV prime
  }
  return h >>> 0
}

// ─── Genre → hue mapping ───────────────────────────────────────────────────

const GENRE_HUES: Record<string, number> = {
  'Science Fiction': 214, // deep blue
  Fantasy: 268, // violet
  Adventure: 152, // green
  Mystery: 222, // slate blue
  Thriller: 18, // ember
  Horror: 348, // crimson
  Romance: 332, // rose
  'Literary Fiction': 260, // indigo
  Fiction: 252, // purple
  'Historical Fiction': 28, // warm amber
  'Self-Help': 42, // gold
  Biography: 168, // teal
  Nonfiction: 196 // cyan
}

const DEFAULT_HUE = 260

const hueFor = (genres?: string[]): number => {
  if (!genres || genres.length === 0) return DEFAULT_HUE
  for (const genre of genres) {
    const hue = GENRE_HUES[genre]
    if (hue !== undefined) return hue
  }
  return DEFAULT_HUE
}

// ─── Helpers ───────────────────────────────────────────────────────────────

const hsl = (h: number, s: number, l: number): string => `hsl(${h} ${s}% ${l}%)`

/**
 * Build the cover palette for a book. Deterministic and cached.
 * @param title  book title (seed for per-book variation)
 * @param genres genre tags (drives base hue)
 * @param seed   extra seed (e.g. book id) to disambiguate same-title books
 */
export const getCoverPalette = (
  title: string,
  genres?: string[],
  seed = ''
): CoverPalette => {
  const cacheKey = `${seed}|${title}|${(genres ?? []).join(',')}`
  const cached = PALETTE_CACHE.get(cacheKey)
  if (cached) return cached

  const baseHue = hueFor(genres)
  const h = hashString(cacheKey)

  const hueOffset = (h % 48) - 24 // -24..23 — per-book variation
  const sat = 55 + (h % 25) // 55..79%
  const lightBase = 38 + (h % 16) // 38..53%
  const hue = (baseHue + hueOffset + 360) % 360

  const from = hsl(hue, sat, Math.min(lightBase + 8, 62))
  const to = hsl((hue + 42) % 360, Math.max(sat - 6, 45), Math.max(lightBase - 14, 20))
  const accent = hsl(hue, sat, Math.max(lightBase - 24, 13))
  // Light palettes get dark text; dark palettes get light text (WCAG-minded)
  const text = lightBase > 52 ? '#1c1917' : '#fafaf9'
  const muted = lightBase > 52 ? 'rgba(28,25,23,0.62)' : 'rgba(250,250,249,0.68)'

  const palette: CoverPalette = { from, to, accent, text, muted, hue }
  PALETTE_CACHE.set(cacheKey, palette)
  return palette
}

const PALETTE_CACHE = new Map<string, CoverPalette>()

/**
 * Two-letter monogram from the title ("Project Hail Mary" → "PH").
 */
export const getBookInitials = (title: string): string => {
  const words = title.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return 'B'
  const first = words[0][0] ?? 'B'
  const second = words.length > 1 ? (words[1][0] ?? '') : ''
  return (first + second).toUpperCase()
}

/**
 * CSS gradient for the cover face.
 */
export const buildCoverBackground = (palette: CoverPalette): string =>
  `linear-gradient(150deg, ${palette.from} 0%, ${palette.to} 100%)`

/**
 * CSS for the subtle dot-pattern texture overlaid on the gradient.
 * Cheap (CSS-only), adds a "designed" print feel.
 */
export const buildDotPattern = (palette: CoverPalette): string =>
  `radial-gradient(circle at 30% 20%, ${palette.text}22 0 1px, transparent 1.5px),` +
  `radial-gradient(circle at 70% 60%, ${palette.text}1a 0 1px, transparent 1.5px),` +
  `radial-gradient(circle at 50% 85%, ${palette.text}14 0 1.5px, transparent 2px)`
