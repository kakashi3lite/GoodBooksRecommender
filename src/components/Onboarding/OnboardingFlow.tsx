/**
 * 🎉 Onboarding Flow — Account Creation + Taste Quiz
 * Chain-of-Thought: Turns a first-time visitor into a personalized reader.
 * Steps: Welcome → Create Account → Taste Quiz → Done (personalized dashboard).
 * Memory: Dispatches register + completeOnboarding so recommendations are
 * personalized immediately after account creation.
 */

import { AnimatePresence, motion } from 'framer-motion'
import {
    ArrowLeft,
    ArrowRight,
    BookOpen,
    Check,
    Heart,
    Sparkles,
    Target,
    Wand2
} from 'lucide-react'
import React, { useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { BOOK_GENRES } from '../../data/bookCatalog'
import { useFocusTrap } from '../../hooks/useFocusTrap'
import { useAppDispatch } from '../../hooks/redux'
import { isValidAccountEmail } from '../../lib/accountApi'
import { completeOnboarding, register, syncAccountToServer } from '../../stores/user/userSlice'
import { READING_PACE, moodsForPace } from '../../utils/readingPace'

const GENRE_EMOJI: Record<string, string> = {
    Fiction: '📖',
    'Science Fiction': '🚀',
    Fantasy: '🐉',
    Mystery: '🕵️',
    Thriller: '🔪',
    Romance: '💖',
    'Literary Fiction': '🖋️',
    'Historical Fiction': '🏛️',
    'Self-Help': '🌱',
    Biography: '👤',
    Nonfiction: '📚',
    Horror: '👻',
    Adventure: '🗺️'
}

const GOALS = [
    { label: 'Light', value: 5, blurb: 'a few great books' },
    { label: 'Steady', value: 12, blurb: 'one a month' },
    { label: 'Avid', value: 24, blurb: 'two a month' },
    { label: 'Bookworm', value: 52, blurb: 'one a week' }
]

interface OnboardingFlowProps {
    /** Optional initial email to prefill the account step. */
    initialEmail?: string
}

/**
 * OnboardingFlow — the first-run experience. Full-screen, animated, 3 steps.
 */
const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ initialEmail = '' }) => {
    const dispatch = useAppDispatch()

    const [step, setStep] = useState(0)
    const [name, setName] = useState('')
    const [email, setEmail] = useState(initialEmail)
    const [genres, setGenres] = useState<string[]>([])
    const [goal, setGoal] = useState(24)
    const [pace, setPace] = useState('mixed')

    // The gate covers a fully interactive dashboard; without a trap, Tab walks
    // straight into controls the reader cannot see.
    const dialogRef = useFocusTrap<HTMLDivElement>(true)

    const canContinue = useMemo(() => {
        if (step === 1) return name.trim().length > 0 && isValidAccountEmail(email)
        if (step === 2) return genres.length > 0
        return true
    }, [step, name, email, genres])

    const toggleGenre = (genre: string) => {
        setGenres((prev) =>
            prev.includes(genre) ? prev.filter((g) => g !== genre) : [...prev, genre]
        )
    }

    const handleFinish = async () => {
        dispatch(register({ name, email }))
        dispatch(
            completeOnboarding({
                favoriteGenres: genres,
                readingGoal: goal,
                preferredFormats: ['ebook', 'print'],
                // The pace question is only honest if the answer is used.
                preferredMoods: moodsForPace(pace)
            })
        )
        // Persist the account now — a new account must never be swallowed by
        // the mount-level debounce. Await it so a conflict is visible: creating
        // an account for an email that already exists is a 409, not a success.
        const sync = await dispatch(syncAccountToServer({ force: true }))
        try {
            sessionStorage.setItem('goodbooks_onboarded', '1')
        } catch {
            // sessionStorage unavailable — gate simply re-shows next load
        }
        if ((sync.payload as { error?: string } | undefined)?.error === 'email_taken') {
            toast.error(
                'That email already has an account. Use a different email to save this profile.'
            )
        } else {
            toast.success(`Welcome, ${name.trim().split(' ')[0]}! Your picks are ready 🎉`)
        }
    }

    /**
     * Guest path — never lock a reader out.
     * Registers a lightweight guest profile (reducer falls back to sensible
     * defaults) and completes onboarding so the full-screen gate opens and
     * every button becomes interactive. A session flag also prevents the gate
     * from reappearing on every reload when localStorage is unavailable
     * (in-app browsers, private mode, cleared storage).
     */
    const skipForNow = () => {
        dispatch(register({ name: '', email: '' }))
        dispatch(
            completeOnboarding({
                favoriteGenres: ['Fiction', 'Science Fiction', 'Mystery'],
                readingGoal: 24,
                preferredFormats: ['ebook', 'print']
            })
        )
        dispatch(syncAccountToServer({ force: true }))
        try {
            sessionStorage.setItem('goodbooks_onboarded', '1')
        } catch {
            // ignore — gate re-shows next load
        }
        toast.success('Exploring as guest — create an account anytime to save your picks 📚')
    }

    const next = () => {
        if (step === 2) {
            handleFinish()
        } else {
            setStep((s) => s + 1)
        }
    }

    const stepTitle = ['Discover books made for you', 'Create your free account', 'What do you love to read?']
    const stepBlurb = [
        'AI-powered recommendations that learn what you love — not what everyone else loves.',
        'No credit card. No spam. Just a reading life that finally feels personal.',
        'Pick a few genres and how much you read. We’ll do the rest.'
    ]

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center overflow-y-auto bg-gradient-to-br from-slate-950 via-blue-950 to-indigo-950 p-4 sm:p-8">
            {/* Ambient glow */}
            <div className="pointer-events-none absolute inset-0 opacity-40 neural-background" />

            <motion.div
                ref={dialogRef}
                initial={{ opacity: 0, y: 24, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className="relative w-full max-w-2xl rounded-3xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-2xl overflow-hidden"
                role="dialog"
                aria-modal="true"
                aria-label="Welcome to GoodBooks"
            >
                {/* Progress header */}
                <div className="px-6 sm:px-10 pt-6">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
                            <BookOpen className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                            GoodBooks
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                            Step {step + 1} of 3
                        </span>
                    </div>
                    <div className="flex gap-1.5">
                        {[0, 1, 2].map((i) => (
                            <div
                                key={i}
                                className={`h-1.5 flex-1 rounded-full transition-colors duration-300 ${i <= step ? 'bg-gradient-to-r from-blue-600 to-purple-600' : 'bg-gray-200 dark:bg-gray-700'
                                    }`}
                            />
                        ))}
                    </div>
                </div>

                <div className="px-6 sm:px-10 py-6 sm:py-8 min-h-[380px]">
                    <AnimatePresence mode="wait">
                        {/* ── Step 0: Welcome ─────────────────────────────────────── */}
                        {step === 0 && (
                            <motion.div
                                key="welcome"
                                initial={{ opacity: 0, x: 24 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -24 }}
                                className="text-center py-6"
                            >
                                <motion.div
                                    initial={{ scale: 0.6, rotate: -8 }}
                                    animate={{ scale: 1, rotate: 0 }}
                                    transition={{ type: 'spring', stiffness: 200, damping: 15 }}
                                    className="w-20 h-20 mx-auto mb-6 rounded-3xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center shadow-xl shadow-blue-500/30"
                                >
                                    <Wand2 className="w-10 h-10 text-white" />
                                </motion.div>
                                <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 dark:text-white mb-3">
                                    Discover books{' '}
                                    <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                                        made for you
                                    </span>
                                </h1>
                                <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto mb-8">
                                    Tell us what you love, and our engine finds books you’ll actually finish —
                                    with reasons, not guesses.
                                </p>

                                <div className="grid grid-cols-3 gap-3 max-w-md mx-auto mb-8">
                                    {[
                                        { icon: Sparkles, label: 'Personalized' },
                                        { icon: Target, label: 'On-target picks' },
                                        { icon: Heart, label: 'Built for readers' }
                                    ].map(({ icon: Icon, label }) => (
                                        <div
                                            key={label}
                                            className="flex flex-col items-center gap-1.5 rounded-2xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 py-3"
                                        >
                                            <Icon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                                            <span className="text-xs font-medium text-gray-700 dark:text-gray-200">
                                                {label}
                                            </span>
                                        </div>
                                    ))}
                                </div>

                                <button
                                    type="button"
                                    onClick={skipForNow}
                                    className="text-sm text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 underline underline-offset-4 transition-colors"
                                >
                                    Skip for now — explore as guest
                                </button>
                            </motion.div>
                        )}

                        {/* ── Step 1: Account ─────────────────────────────────────── */}
                        {step === 1 && (
                            <motion.div
                                key="account"
                                initial={{ opacity: 0, x: 24 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -24 }}
                                className="py-4"
                            >
                                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1.5">
                                    Create your account
                                </h2>
                                <p className="text-gray-600 dark:text-gray-400 mb-6 text-sm">
                                    Takes 30 seconds. Your recommendations get smarter with every pick.
                                </p>

                                <div className="space-y-4">
                                    <label className="block">
                                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Your name
                                        </span>
                                        <input
                                            type="text"
                                            value={name}
                                            onChange={(e) => setName(e.target.value)}
                                            placeholder="Ada Lovelace"
                                            className="mt-1.5 w-full px-4 py-3 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 outline-none text-gray-900 dark:text-white transition-colors"
                                        />
                                    </label>
                                    <label className="block">
                                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Email address
                                        </span>
                                        <input
                                            type="email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            placeholder="ada@example.com"
                                            className="mt-1.5 w-full px-4 py-3 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 outline-none text-gray-900 dark:text-white transition-colors"
                                        />
                                    </label>
                                </div>
                            </motion.div>
                        )}

                        {/* ── Step 2: Taste quiz ──────────────────────────────────── */}
                        {step === 2 && (
                            <motion.div
                                key="taste"
                                initial={{ opacity: 0, x: 24 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -24 }}
                                className="py-2"
                            >
                                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1.5">
                                    What do you love to read?
                                </h2>
                                <p className="text-gray-600 dark:text-gray-400 mb-5 text-sm">
                                    Pick at least one genre — the more you pick, the sharper your picks get.
                                </p>

                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 mb-6">
                                    {BOOK_GENRES.map((genre) => {
                                        const active = genres.includes(genre)
                                        return (
                                            <button
                                                key={genre}
                                                onClick={() => toggleGenre(genre)}
                                                className={`flex items-center gap-2 px-3 py-2.5 rounded-xl border text-sm font-medium transition-all ${active
                                                    ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 shadow-sm'
                                                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:border-blue-400'
                                                    }`}
                                                aria-pressed={active}
                                            >
                                                <span className="text-base">{GENRE_EMOJI[genre] ?? '📚'}</span>
                                                <span className="truncate">{genre}</span>
                                                {active && <Check className="w-4 h-4 ml-auto flex-shrink-0" />}
                                            </button>
                                        )
                                    })}
                                </div>

                                {/* Reading goal */}
                                <div className="mb-6">
                                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                        Reading goal
                                    </span>
                                    <div className="grid grid-cols-4 gap-2 mt-2">
                                        {GOALS.map((g) => (
                                            <button
                                                key={g.value}
                                                onClick={() => setGoal(g.value)}
                                                className={`px-2 py-2.5 rounded-xl border text-center transition-all ${goal === g.value
                                                    ? 'border-purple-600 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                                                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:border-purple-400'
                                                    }`}
                                            >
                                                <span className="block font-bold text-lg leading-tight">{g.value}</span>
                                                <span className="block text-[11px] opacity-80">{g.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Pace */}
                                <div className="mb-2">
                                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                        How do you like to read?
                                    </span>
                                    <div className="grid grid-cols-3 gap-2 mt-2">
                                        {READING_PACE.map((p) => (
                                            <button
                                                key={p.id}
                                                onClick={() => setPace(p.id)}
                                                className={`px-2 py-2.5 rounded-xl border text-center transition-all ${pace === p.id
                                                    ? 'border-green-600 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                                                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:border-green-400'
                                                    }`}
                                            >
                                                <span className="block text-sm font-semibold">{p.label}</span>
                                                <span className="block text-[11px] opacity-75">{p.blurb}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Footer actions */}
                <div className="px-6 sm:px-10 pb-6 flex items-center justify-between">
                    <button
                        onClick={() => setStep((s) => Math.max(0, s - 1))}
                        className={`inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors ${step === 0
                            ? 'invisible'
                            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                            }`}
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back
                    </button>

                    <motion.button
                        whileTap={{ scale: 0.97 }}
                        onClick={next}
                        disabled={!canContinue}
                        className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-semibold shadow-lg shadow-blue-500/25 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
                    >
                        {step === 2 ? (
                            <>
                                Show me my books
                                <Wand2 className="w-4 h-4" />
                            </>
                        ) : (
                            <>
                                Continue
                                <ArrowRight className="w-4 h-4" />
                            </>
                        )}
                    </motion.button>
                </div>

                {/* Step copy at bottom */}
                <div className="px-6 sm:px-10 pb-6 text-center">
                    <AnimatePresence mode="wait">
                        <motion.div key={step} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                <span className="font-semibold text-gray-700 dark:text-gray-200">
                                    {stepTitle[step]}
                                </span>{' '}
                                — {stepBlurb[step]}
                            </p>
                        </motion.div>
                    </AnimatePresence>
                </div>
            </motion.div>
        </div>
    )
}

export default OnboardingFlow
