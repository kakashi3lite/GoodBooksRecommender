/**
 * 📚 Curated Book Catalog
 * Chain-of-Thought: A typed, offline catalog that powers personalized
 * recommendations even before the ML backend is wired. Each book carries
 * genre + mood signals so the personalization engine can rank them.
 * Forward-Thinking: This is the seed catalog — the backend /api/books/*
 * endpoint will eventually supersede it with the full Goodreads dataset.
 */

export type BookMood =
    | 'cozy'
    | 'fast-paced'
    | 'dark'
    | 'uplifting'
    | 'thought-provoking'
    | 'funny'
    | 'emotional'
    | 'adventurous'
    | 'mysterious'
    | 'romantic'
    | 'epic'
    | 'quiet'

export interface CatalogBook {
    id: string
    title: string
    authors: string
    cover_url: string
    rating: number
    ratingsCount: number
    genres: string[]
    moods: BookMood[]
    published_year: number
    page_count: number
    description: string
}

export const BOOK_GENRES = [
    'Fiction',
    'Science Fiction',
    'Fantasy',
    'Mystery',
    'Thriller',
    'Romance',
    'Literary Fiction',
    'Historical Fiction',
    'Self-Help',
    'Biography',
    'Nonfiction',
    'Horror',
    'Adventure'
] as const

export const BOOK_MOODS: BookMood[] = [
    'cozy',
    'fast-paced',
    'dark',
    'uplifting',
    'thought-provoking',
    'funny',
    'emotional',
    'adventurous',
    'mysterious',
    'romantic',
    'epic',
    'quiet'
]

/**
 * Seed catalog — 24 books spanning the major genres with rich mood metadata.
 */
export const BOOK_CATALOG: CatalogBook[] = [
    {
        id: 'b-01',
        title: 'The Midnight Library',
        authors: 'Matt Haig',
        cover_url: '',
        rating: 4.3,
        ratingsCount: 120000,
        genres: ['Fiction', 'Literary Fiction'],
        moods: ['thought-provoking', 'emotional', 'uplifting'],
        published_year: 2020,
        page_count: 288,
        description:
            'Between life and death there is a library, and within that library, the shelves go on forever.'
    },
    {
        id: 'b-02',
        title: 'Project Hail Mary',
        authors: 'Andy Weir',
        cover_url: '',
        rating: 4.7,
        ratingsCount: 98000,
        genres: ['Science Fiction', 'Adventure'],
        moods: ['adventurous', 'funny', 'fast-paced', 'uplifting'],
        published_year: 2021,
        page_count: 496,
        description:
            'A lone astronaut must save humanity in this near-perfect sci-fi thriller packed with hard science and heart.'
    },
    {
        id: 'b-03',
        title: 'Tomorrow, and Tomorrow, and Tomorrow',
        authors: 'Gabrielle Zevin',
        cover_url: '',
        rating: 4.5,
        ratingsCount: 85000,
        genres: ['Fiction', 'Literary Fiction'],
        moods: ['emotional', 'thought-provoking', 'quiet'],
        published_year: 2022,
        page_count: 416,
        description:
            'A decade-spanning story about friendship, creativity, and the worlds we build together.'
    },
    {
        id: 'b-04',
        title: 'The House in the Cerulean Sea',
        authors: 'T.J. Klune',
        cover_url: '',
        rating: 4.6,
        ratingsCount: 76000,
        genres: ['Fantasy', 'Fiction'],
        moods: ['cozy', 'uplifting', 'funny', 'emotional'],
        published_year: 2020,
        page_count: 400,
        description:
            'A caseworker journeys to a remote island orphanage for magical children in this cozy, heartwarming tale.'
    },
    {
        id: 'b-05',
        title: 'Piranesi',
        authors: 'Susanna Clarke',
        cover_url: '',
        rating: 4.4,
        ratingsCount: 42000,
        genres: ['Fantasy', 'Mystery'],
        moods: ['mysterious', 'thought-provoking', 'quiet', 'dark'],
        published_year: 2020,
        page_count: 272,
        description:
            'A man lives in an endless house of halls and statues, and the mystery of his world slowly unfolds.'
    },
    {
        id: 'b-06',
        title: 'A Psalm for the Wild-Built',
        authors: 'Becky Chambers',
        cover_url: '',
        rating: 4.4,
        ratingsCount: 31000,
        genres: ['Science Fiction', 'Fantasy'],
        moods: ['cozy', 'quiet', 'uplifting', 'thought-provoking'],
        published_year: 2021,
        page_count: 160,
        description:
            'A tea monk and a robot explore what it means to be alive in a gentle, hopeful novella.'
    },
    {
        id: 'b-07',
        title: 'The Silent Patient',
        authors: 'Alex Michaelides',
        cover_url: '',
        rating: 4.6,
        ratingsCount: 150000,
        genres: ['Mystery', 'Thriller'],
        moods: ['mysterious', 'fast-paced', 'dark'],
        published_year: 2019,
        page_count: 336,
        description:
            "A woman's act of violence against her husband, and her refusal to speak a single word about it."
    },
    {
        id: 'b-08',
        title: 'Educated',
        authors: 'Tara Westover',
        cover_url: '',
        rating: 4.8,
        ratingsCount: 200000,
        genres: ['Biography', 'Nonfiction'],
        moods: ['emotional', 'thought-provoking', 'uplifting'],
        published_year: 2018,
        page_count: 352,
        description:
            'A memoir about education, family, and the struggle for self-invention.'
    },
    {
        id: 'b-09',
        title: 'Where the Crawdads Sing',
        authors: 'Delia Owens',
        cover_url: '',
        rating: 4.5,
        ratingsCount: 180000,
        genres: ['Fiction', 'Mystery', 'Historical Fiction'],
        moods: ['emotional', 'mysterious', 'quiet'],
        published_year: 2018,
        page_count: 384,
        description:
            'A coming-of-age mystery set in the marshlands of North Carolina.'
    },
    {
        id: 'b-10',
        title: 'The Seven Husbands of Evelyn Hugo',
        authors: 'Taylor Jenkins Reid',
        cover_url: '',
        rating: 4.8,
        ratingsCount: 160000,
        genres: ['Fiction', 'Historical Fiction', 'Romance'],
        moods: ['emotional', 'romantic', 'thought-provoking'],
        published_year: 2017,
        page_count: 400,
        description:
            "Hollywood's golden age, and the secrets of a reclusive icon, told to an unknown journalist."
    },
    {
        id: 'b-11',
        title: 'Dune',
        authors: 'Frank Herbert',
        cover_url: '',
        rating: 4.3,
        ratingsCount: 250000,
        genres: ['Science Fiction', 'Fantasy'],
        moods: ['epic', 'dark', 'thought-provoking', 'adventurous'],
        published_year: 1965,
        page_count: 688,
        description:
            'The epic desert planet saga of politics, religion, and survival.'
    },
    {
        id: 'b-12',
        title: 'The Name of the Wind',
        authors: 'Patrick Rothfuss',
        cover_url: '',
        rating: 4.6,
        ratingsCount: 180000,
        genres: ['Fantasy', 'Adventure'],
        moods: ['epic', 'adventurous', 'emotional'],
        published_year: 2007,
        page_count: 662,
        description:
            'The riveting first-person narrative of Kvothe, a magically gifted young man.'
    },
    {
        id: 'b-13',
        title: 'Gone Girl',
        authors: 'Gillian Flynn',
        cover_url: '',
        rating: 4.2,
        ratingsCount: 220000,
        genres: ['Thriller', 'Mystery'],
        moods: ['dark', 'fast-paced', 'mysterious'],
        published_year: 2012,
        page_count: 432,
        description: "On their fifth wedding anniversary, Nick's wife disappears."
    },
    {
        id: 'b-14',
        title: 'The Thursday Murder Club',
        authors: 'Richard Osman',
        cover_url: '',
        rating: 4.3,
        ratingsCount: 90000,
        genres: ['Mystery', 'Fiction'],
        moods: ['cozy', 'funny', 'mysterious'],
        published_year: 2020,
        page_count: 400,
        description:
            'Four unlikely retirees meet weekly to solve cold cases — and stumble onto a real murder.'
    },
    {
        id: 'b-15',
        title: 'The Song of Achilles',
        authors: 'Madeline Miller',
        cover_url: '',
        rating: 4.6,
        ratingsCount: 140000,
        genres: ['Historical Fiction', 'Romance', 'Fantasy'],
        moods: ['emotional', 'romantic', 'epic', 'dark'],
        published_year: 2011,
        page_count: 416,
        description:
            'A beautiful retelling of the Iliad, centered on the bond between Achilles and Patroclus.'
    },
    {
        id: 'b-16',
        title: 'Atomic Habits',
        authors: 'James Clear',
        cover_url: '',
        rating: 4.9,
        ratingsCount: 300000,
        genres: ['Self-Help', 'Nonfiction'],
        moods: ['uplifting', 'thought-provoking'],
        published_year: 2018,
        page_count: 320,
        description: 'Tiny changes, remarkable results — the definitive guide to habit formation.'
    },
    {
        id: 'b-17',
        title: 'The Invisible Life of Addie LaRue',
        authors: 'V.E. Schwab',
        cover_url: '',
        rating: 4.4,
        ratingsCount: 110000,
        genres: ['Fantasy', 'Historical Fiction', 'Romance'],
        moods: ['emotional', 'romantic', 'thought-provoking', 'dark'],
        published_year: 2020,
        page_count: 448,
        description:
            'A girl who makes a deal to live forever — but is cursed to be forgotten by everyone she meets.'
    },
    {
        id: 'b-18',
        title: 'The Martian',
        authors: 'Andy Weir',
        cover_url: '',
        rating: 4.6,
        ratingsCount: 240000,
        genres: ['Science Fiction', 'Adventure'],
        moods: ['funny', 'fast-paced', 'adventurous', 'uplifting'],
        published_year: 2014,
        page_count: 384,
        description:
            'Stranded on Mars, Mark Watney must science his way back to survival.'
    },
    {
        id: 'b-19',
        title: 'Normal People',
        authors: 'Sally Rooney',
        cover_url: '',
        rating: 4.0,
        ratingsCount: 130000,
        genres: ['Literary Fiction', 'Romance', 'Fiction'],
        moods: ['emotional', 'romantic', 'quiet', 'thought-provoking'],
        published_year: 2018,
        page_count: 288,
        description:
            'The tender, complicated relationship between two people who keep finding their way back to each other.'
    },
    {
        id: 'b-20',
        title: 'The Southern Book Club\'s Guide to Slaying Vampires',
        authors: 'Grady Hendrix',
        cover_url: '',
        rating: 4.1,
        ratingsCount: 45000,
        genres: ['Horror', 'Fiction'],
        moods: ['dark', 'funny', 'fast-paced'],
        published_year: 2020,
        page_count: 416,
        description:
            'A book club of Southern housewives discovers a vampire in their neighborhood — and decides to fight back.'
    },
    {
        id: 'b-21',
        title: 'Circe',
        authors: 'Madeline Miller',
        cover_url: '',
        rating: 4.5,
        ratingsCount: 150000,
        genres: ['Fantasy', 'Historical Fiction', 'Literary Fiction'],
        moods: ['epic', 'emotional', 'thought-provoking'],
        published_year: 2018,
        page_count: 416,
        description:
            'The story of the mythological witch Circe, from exile to self-discovery.'
    },
    {
        id: 'b-22',
        title: 'Sapiens',
        authors: 'Yuval Noah Harari',
        cover_url: '',
        rating: 4.4,
        ratingsCount: 280000,
        genres: ['Nonfiction', 'Self-Help'],
        moods: ['thought-provoking'],
        published_year: 2011,
        page_count: 464,
        description: 'A sweeping history of humankind — how we got here and where we might go.'
    },
    {
        id: 'b-23',
        title: 'The Guest List',
        authors: 'Lucy Foley',
        cover_url: '',
        rating: 4.1,
        ratingsCount: 60000,
        genres: ['Mystery', 'Thriller'],
        moods: ['mysterious', 'fast-paced', 'dark'],
        published_year: 2020,
        page_count: 336,
        description:
            'A wedding on a remote island turns deadly — and everyone has a secret.'
    },
    {
        id: 'b-24',
        title: 'Beach Read',
        authors: 'Emily Henry',
        cover_url: '',
        rating: 4.2,
        ratingsCount: 80000,
        genres: ['Romance', 'Fiction'],
        moods: ['cozy', 'romantic', 'funny', 'uplifting'],
        published_year: 2020,
        page_count: 384,
        description:
            'Two rival writers swap genres for the summer — and fall for each other.'
    }
]

/** Convenience: genre → matching books for fast lookups. */
export const booksByGenre = (genre: string): CatalogBook[] =>
    BOOK_CATALOG.filter((b) => b.genres.includes(genre))

/** Convenience: single-book lookup by id. */
export const getBookById = (id: string): CatalogBook | undefined =>
    BOOK_CATALOG.find((b) => b.id === id)
