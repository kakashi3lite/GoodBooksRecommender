/**
 * 🧩 Bento grid placement helper.
 * Chain-of-Thought: gives each card a distinctive size (hero / wide / tall /
 * standard) so recommendation + trending grids feel editorial instead of a
 * monotonous uniform grid. The pattern repeats every 8 items and pairs with
 * the `.bento-*` classes in dashboard/css/book-card.css.
 */

export interface BentoPlacement {
    className: 'bento-hero' | 'bento-wide' | 'bento-tall' | 'bento-standard'
    /** Featured cards use the larger BookCard variant (open blurb, wide cover). */
    featured: boolean
}

/** Assign a placement by index — deterministic, responsive at every breakpoint. */
export const bentoPlacement = (index: number): BentoPlacement => {
    const mod = index % 8
    if (mod === 0) return { className: 'bento-hero', featured: true }
    if (mod === 1 || mod === 5) return { className: 'bento-wide', featured: false }
    if (mod === 3 || mod === 6) return { className: 'bento-tall', featured: false }
    return { className: 'bento-standard', featured: false }
}
