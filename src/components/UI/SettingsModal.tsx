/**
 * ⚙️ Settings — a real, functional settings panel (not a "coming soon" toast).
 * Chain-of-Thought: readers need control over their environment. This modal
 * wires directly to the stores:
 *   - Appearance → dashboardSlice.setTheme (light/dark/system)
 *   - Reading   → userSlice.setPreferences (goal, notifications, privacy)
 *   - Account   → shows the signed-in reader
 *   - Data      → export your library as JSON (reader-owned data)
 * All changes persist immediately (Redux → localStorage).
 */

import { BookOpen, Download, Eye, Moon, Palette, Shield, Sun, Trash2, User, X } from 'lucide-react'
import { useFocusTrap } from '../../hooks/useFocusTrap'
import React, { useState } from 'react'
import toast from 'react-hot-toast'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import { getAccountKey } from '../../lib/accountApi'
import { deleteUserAccount } from '../../lib/userRepository'
import { setTheme } from '../../stores/dashboard/dashboardSlice'
import {
    logout,
    setPreferences,
    syncAccountToServer,
    type UserPreferences
} from '../../stores/user/userSlice'
import { READING_PACE, moodsForPace, paceForMoods } from '../../utils/readingPace'

interface SettingsModalProps {
    open: boolean
    onClose: () => void
}

const GOAL_PRESETS = [5, 12, 24, 52]

const SettingsModal: React.FC<SettingsModalProps> = ({ open, onClose }) => {
    const dispatch = useAppDispatch()
    const theme = useAppSelector((state) => state.dashboard.theme)
    const preferences = useAppSelector((state) => state.user.preferences)
    const profile = useAppSelector((state) => state.user.profile)
    const readingState = useAppSelector((state) => state.reading)
    const [goalInput, setGoalInput] = useState(String(preferences.readingGoal))
    const pace = paceForMoods(preferences.preferredMoods)

    // `aria-modal` is only honest when Tab cannot escape the dialog.
    // Declared before any early return — a hook after a conditional
    // return would break React's hook order when the modal toggles.
    const dialogRef = useFocusTrap<HTMLDivElement>(open, onClose)

    const [confirmDelete, setConfirmDelete] = useState(false)

    // A D1 row is only writable from this device while its account key is
    // present; without one the account is local-only and there is nothing to
    // sync (and no server copy to delete).
    const hasServerAccount = Boolean(getAccountKey(profile.email))

    if (!open) return null

    /**
     * Apply a preference and mirror it to D1 immediately — a reader who sets a
     * new goal must not lose it because the 5-minute mount debounce swallowed
     * the write.
     */
    const persistPreferences = (patch: Partial<UserPreferences>) => {
        dispatch(setPreferences(patch))
        if (hasServerAccount) dispatch(syncAccountToServer({ force: true }))
    }

    const setGoal = (value: number) => {
        const goal = Math.max(1, Math.min(365, Math.round(value)))
        setGoalInput(String(goal))
        persistPreferences({ readingGoal: goal })
        toast.success(`Reading goal set to ${goal} books/year 🎯`)
    }

    const deleteMyAccount = async () => {
        if (!confirmDelete) {
            setConfirmDelete(true)
            return
        }
        const removedFromServer = await deleteUserAccount(profile.email)
        dispatch(logout())
        setConfirmDelete(false)
        onClose()
        toast.success(
            removedFromServer
                ? 'Account deleted from Cloudflare'
                : 'Local account cleared'
        )
    }

    const exportData = () => {
        const payload = {
            exportedAt: new Date().toISOString(),
            profile,
            preferences,
            reading: readingState
        }
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'goodbooks-export.json'
        a.click()
        URL.revokeObjectURL(url)
        toast.success('Your reading library exported 📦')
    }

    const themes: Array<{ id: 'light' | 'dark' | 'auto'; label: string; icon: typeof Sun }> = [
        { id: 'light', label: 'Light', icon: Sun },
        { id: 'dark', label: 'Dark', icon: Moon },
        { id: 'auto', label: 'Auto', icon: Palette }
    ]

    return (
        <div
            className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label="Settings"
            onClick={onClose}
        >
            <div
                className="w-full max-w-md max-h-[88vh] overflow-y-auto rounded-3xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-2xl"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-900 rounded-t-3xl">
                    <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <SettingsIcon /> Settings
                    </h2>
                    <button
                        type="button"
                        onClick={onClose}
                        aria-label="Close settings"
                        className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="px-6 py-5 space-y-6">
                    {/* Appearance */}
                    <section>
                        <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                            <Palette className="w-4 h-4 text-blue-600" /> Appearance
                        </h3>
                        <div className="grid grid-cols-3 gap-2">
                            {themes.map((t) => (
                                <button
                                    key={t.id}
                                    type="button"
                                    onClick={() => {
                                        dispatch(setTheme(t.id))
                                        toast.success(`${t.label} mode ${t.id === 'auto' ? '(follows system)' : 'enabled'}`)
                                    }}
                                    className={`flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl border text-sm font-medium transition-colors ${theme === t.id
                                            ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                                            : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
                                        }`}
                                >
                                    <t.icon className="w-4 h-4" />
                                    {t.label}
                                </button>
                            ))}
                        </div>
                    </section>

                    {/* Reading preferences */}
                    <section>
                        <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                            <BookOpen className="w-4 h-4 text-green-600" /> Reading
                        </h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">
                                    Yearly reading goal (books)
                                </label>
                                <div className="flex gap-2">
                                    {GOAL_PRESETS.map((g) => (
                                        <button
                                            key={g}
                                            type="button"
                                            onClick={() => setGoal(g)}
                                            className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-colors ${preferences.readingGoal === g
                                                    ? 'bg-green-600 text-white'
                                                    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-green-50 dark:hover:bg-green-900/30'
                                                }`}
                                        >
                                            {g}
                                        </button>
                                    ))}
                                </div>
                                <div className="flex items-center gap-2 mt-2">
                                    <input
                                        type="number"
                                        min={1}
                                        max={365}
                                        value={goalInput}
                                        onChange={(e) => setGoalInput(e.target.value)}
                                        onBlur={() => setGoal(Number(goalInput) || preferences.readingGoal)}
                                        aria-label="Custom reading goal"
                                        className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-green-500"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setGoal(Number(goalInput) || preferences.readingGoal)}
                                        className="px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-700"
                                    >
                                        Set
                                    </button>
                                </div>
                            </div>

                            {/* The pace question onboarding asks, revisitable.
                                Without this the answer was frozen forever: a reader
                                who picked "Quick reads" once could never say
                                otherwise, and the preference silently ranked every
                                recommendation they saw. */}
                            <div>
                                <span className="block text-sm text-gray-700 dark:text-gray-200 mb-1.5">
                                    Reading pace
                                </span>
                                <div className="grid grid-cols-3 gap-2" role="group" aria-label="Reading pace">
                                    {READING_PACE.map((option) => {
                                        const active = pace === option.id
                                        return (
                                            <button
                                                key={option.id}
                                                type="button"
                                                aria-pressed={active}
                                                onClick={() => {
                                                    persistPreferences({ preferredMoods: moodsForPace(option.id) })
                                                    toast.success(`Pace set to ${option.label}`)
                                                }}
                                                className={`px-2 py-2.5 rounded-lg border text-center transition-colors ${active
                                                    ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                                                    : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
                                                    }`}
                                            >
                                                <span className="block text-xs font-semibold">{option.label}</span>
                                                <span className="block text-[10px] opacity-75">{option.blurb}</span>
                                            </button>
                                        )
                                    })}
                                </div>
                            </div>

                            <label className="flex items-center justify-between py-2">
                                <span className="text-sm text-gray-700 dark:text-gray-200">
                                    Notifications &amp; streak reminders
                                </span>
                                <button
                                    type="button"
                                    role="switch"
                                    aria-checked={preferences.notifications}
                                    onClick={() => {
                                        dispatch(setPreferences({ notifications: !preferences.notifications }))
                                        toast.success(
                                            preferences.notifications ? 'Notifications off' : 'Notifications on'
                                        )
                                    }}
                                    className={`relative w-12 h-7 rounded-full transition-colors ${preferences.notifications ? 'bg-green-600' : 'bg-gray-300 dark:bg-gray-600'
                                        }`}
                                >
                                    <span
                                        className={`absolute top-1 w-5 h-5 rounded-full bg-white shadow transition-all ${preferences.notifications ? 'left-6' : 'left-1'
                                            }`}
                                    />
                                </button>
                            </label>

                            <div>
                                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1.5">
                                    Profile visibility
                                </label>
                                <div className="grid grid-cols-3 gap-2">
                                    {(['public', 'friends', 'private'] as const).map((p) => (
                                        <button
                                            key={p}
                                            type="button"
                                            onClick={() => dispatch(setPreferences({ privacy: p }))}
                                            className={`flex items-center justify-center gap-1 px-3 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${preferences.privacy === p
                                                    ? 'border border-blue-600 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                                                    : 'border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
                                                }`}
                                        >
                                            <Eye className="w-3.5 h-3.5" /> {p}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Account */}
                    <section>
                        <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                            <User className="w-4 h-4 text-purple-600" /> Account
                        </h3>
                        <div className="rounded-xl bg-gray-50 dark:bg-gray-800 p-3 text-sm">
                            <p className="font-medium text-gray-900 dark:text-white">{profile.name}</p>
                            <p className="text-gray-500 dark:text-gray-400">{profile.email}</p>
                            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                                Reading level: {profile.readingLevel}
                            </p>
                            <p
                                className={`text-xs mt-2 ${hasServerAccount ? 'text-green-700 dark:text-green-400' : 'text-amber-700 dark:text-amber-400'}`}
                                data-testid="account-persistence"
                            >
                                {hasServerAccount
                                    ? 'Saved to Cloudflare — survives clearing this browser.'
                                    : 'Local only — complete onboarding with a valid email to save it to Cloudflare.'}
                            </p>
                        </div>
                        <button
                            type="button"
                            onClick={deleteMyAccount}
                            className="mt-3 w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-red-300 dark:border-red-800 text-red-700 dark:text-red-400 text-sm font-medium hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                        >
                            <Trash2 className="w-4 h-4" />
                            {confirmDelete ? 'Tap again to confirm deletion' : 'Delete my account'}
                        </button>
                    </section>

                    {/* Data */}
                    <section>
                        <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                            <Shield className="w-4 h-4 text-green-600" /> Your data
                        </h3>
                        <button
                            type="button"
                            onClick={exportData}
                            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                        >
                            <Download className="w-4 h-4" /> Export my reading library
                        </button>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                            Your library lives in this browser (localStorage) and your account is mirrored
                            to Cloudflare. Export to keep a personal copy.
                        </p>
                    </section>
                </div>
            </div>
        </div>
    )
}

/** Small local icon so the header is self-contained. */
const SettingsIcon: React.FC = () => (
    <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
)

export default SettingsModal
