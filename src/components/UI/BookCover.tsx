/**
 * 📕 BookCover — intelligent, performant book cover
 * Chain-of-Thought:
 *   Layer 1 — a deterministic generated cover (genre-tinted gradient + serif
 *            typography + subtle texture) renders instantly for EVERY book.
 *   Layer 2 — when a real `coverUrl` exists, an `<img>` (lazy, async-decoded)
 *            fades in over the generated base; on error it hides, revealing the
 *            generated art — so users NEVER see a broken-image icon.
 *
 * Reader-psychology notes:
 *   - A one-shot shimmer pulses over the generated base while the real image
 *     downloads — a "cover is loading" signal beats a static placeholder
 *     (perceived performance; the eye knows progress is happening).
 *   - The real cover fades + gently scales in on load — recognition is the
 *     reward, and the motion keeps the transition from feeling abrupt.
 *   - `fetchPriority="high"` on hero/featured covers lowers Largest
 *     Contentful Paint for the most visible cover on the page.
 *
 * Performance / UX properties:
 *   - Fixed 2:3 aspect ratio → zero layout shift (no CLS)
 *   - Palette is memoized in coverArt → O(1) after first render
 *   - CSS gradients + patterns only → GPU-cheap, no network for generated covers
 *   - `loading="lazy"` + `decoding="async"` for real images
 *   - Deterministic → same book, same cover, every session (brand consistency)
 */

import React, { useMemo, useState } from 'react'
import {
    buildCoverBackground,
    buildDotPattern,
    getBookInitials,
    getCoverPalette
} from '../../utils/coverArt'

type CoverSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'
type CoverRadius = 'sm' | 'md' | 'lg' | 'none'
type FetchPriority = 'high' | 'low' | 'auto'

interface BookCoverProps {
    title: string
    author?: string
    /** Real cover URL. When present it fades in over the generated base. */
    coverUrl?: string
    /** Genre tags drive the cover's base hue. */
    genres?: string[]
    /** Extra seed (book id) to disambiguate same-title books. */
    seed?: string
    alt?: string
    size?: CoverSize
    rounded?: CoverRadius
    /** Show the title/author typography (auto-hidden on xs). */
    showText?: boolean
    /** Hint the browser about image fetch priority (hero covers → high). */
    fetchPriority?: FetchPriority
    className?: string
}

const SIZE_CLASSES: Record<CoverSize, string> = {
    xs: 'w-12 aspect-[2/3]',
    sm: 'w-20 sm:w-24 aspect-[2/3]',
    md: 'w-28 sm:w-32 aspect-[2/3]',
    lg: 'w-40 sm:w-44 aspect-[2/3]',
    xl: 'w-52 sm:w-56 aspect-[2/3]'
}

const RADIUS_CLASSES: Record<CoverRadius, string> = {
    sm: 'rounded-md',
    md: 'rounded-lg',
    lg: 'rounded-xl',
    none: 'rounded-none'
}

/**
 * BookCover — a cover that is always beautiful: generated art by default,
 * real imagery when available, and never a broken placeholder.
 */
const BookCover: React.FC<BookCoverProps> = ({
    title,
    author,
    coverUrl,
    genres,
    seed,
    alt,
    size = 'md',
    rounded = 'lg',
    showText = true,
    fetchPriority = 'auto',
    className = ''
}) => {
    const palette = useMemo(
        () => getCoverPalette(title, genres, seed),
        [title, genres, seed]
    )
    const initials = useMemo(() => getBookInitials(title), [title])
    // Track the real-image lifecycle so we can show a loading shimmer and a
    // smooth fade-in, and NEVER show a broken image (error keeps generated art).
    const [imageState, setImageState] = useState<'loading' | 'loaded' | 'error'>(
        coverUrl ? 'loading' : 'error'
    )
    // Reset when the cover URL changes — a BookCover instance can be reused
    // for a different book (list recycling), and stale 'loaded' would hide the
    // new cover's generated base until its own image resolves.
    React.useEffect(() => {
        setImageState(coverUrl ? 'loading' : 'error')
    }, [coverUrl])

    const background = buildCoverBackground(palette)
    const pattern = buildDotPattern(palette)
    const label = alt ?? `Cover of ${title}`

    return (
        <div
            role="img"
            aria-label={label}
            className={`relative overflow-hidden shrink-0 select-none shadow-md ${SIZE_CLASSES[size]} ${RADIUS_CLASSES[rounded]} ${className}`}
            style={{ background, boxShadow: `0 8px 20px -6px ${palette.accent}66` }}
        >
            {/* Texture: soft dot pattern */}
            <div className="absolute inset-0" style={{ backgroundImage: pattern }} />

            {/* Soft radial glow, top-left */}
            <div
                className="absolute inset-0"
                style={{
                    background:
                        'radial-gradient(120% 60% at 18% 12%, rgba(255,255,255,0.22) 0%, rgba(255,255,255,0) 55%)'
                }}
            />

            {/* Spine edge */}
            <div
                className="absolute left-0 top-0 bottom-0 w-[7%]"
                style={{ background: palette.accent }}
            >
                <div className="absolute left-0 top-0 bottom-0 w-px bg-white/20" />
            </div>

            {/* Centered monogram */}
            <div className="absolute inset-0 flex items-center justify-center pl-[4%]">
                <span
                    className="font-serif font-semibold tracking-tight"
                    style={{
                        color: palette.text,
                        opacity: 0.9,
                        fontSize: 'min(34%, 3.4rem)'
                    }}
                >
                    {initials}
                </span>
            </div>

            {/* Bottom scrim + typography */}
            {showText && size !== 'xs' && (
                <div
                    className="absolute inset-x-0 bottom-0 px-[10%] pb-[8%] pt-[22%]"
                    style={{
                        background:
                            'linear-gradient(to top, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0) 100%)'
                    }}
                >
                    <p
                        className="font-serif font-semibold leading-tight"
                        style={{ color: '#fafaf9', fontSize: 'min(13%, 0.95rem)' }}
                        title={title}
                    >
                        {title}
                    </p>
                    {author && (
                        <p
                            className="truncate font-sans text-[10px] leading-relaxed"
                            style={{ color: 'rgba(250,250,249,0.72)' }}
                        >
                            {author}
                        </p>
                    )}
                </div>
            )}

            {/* Real image overlay — fades in over the generated base */}
            {coverUrl ? (
                <>
                    {/* One-shot loading shimmer: signals the real cover is
                        coming while the generated art shows through. */}
                    {imageState === 'loading' && (
                        <div
                            aria-hidden="true"
                            className="absolute inset-0 animate-pulse bg-white/10"
                        />
                    )}
                    <img
                        src={coverUrl}
                        alt={label}
                        loading="lazy"
                        decoding="async"
                        // React 18.3.1 warns on the camelCase `fetchPriority`
                        // prop, so we pass the lowercase HTML attribute.
                        {...({ fetchpriority: fetchPriority } as React.ImgHTMLAttributes<HTMLImageElement>)}
                        onLoad={() => setImageState('loaded')}
                        onError={() => setImageState('error')}
                        className={`absolute inset-0 h-full w-full object-cover transition-all duration-300 ${imageState === 'loaded'
                            ? 'opacity-100 scale-100'
                            : 'opacity-0 scale-95'
                            }`}
                    />
                </>
            ) : null}
        </div>
    )
}

export default BookCover
