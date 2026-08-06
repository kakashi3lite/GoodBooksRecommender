/**
 * 📚 AI Book Recommendations Component
 * Chain-of-Thought: Fetch personalized recommendations through Redux and render
 * them in a responsive grid with loading / error / empty states.
 * Memory: Track viewed recommendations to mark new items
 * Forward-Thinking: Strategy and genre filters plug directly into the backend
 */

import React, { useEffect, useMemo, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import {
  addToRecentRecommendations,
  fetchRecommendations,
  setError,
  setLoading
} from '../../stores/books/booksSlice';
import { getPersonalizedRecommendations } from '../../utils/personalization';
import { BookCard } from '../UI/BookCard';
import { ErrorMessage } from '../UI/ErrorMessage';
import { LoadingSpinner } from '../UI/LoadingSpinner';

// Type definitions (aligned with the books slice Book shape)
interface Book {
  id: string;
  title: string;
  authors: string;
  cover_url: string;
  rating: number;
  genres: string[];
  published_year: number;
  description: string;
  ai_recommendation_score?: number;
  ai_explanation?: string;
}

interface RecommendationProps {
  userId?: string;
  limit?: number;
  strategy?: 'collaborative' | 'content' | 'hybrid' | 'neural';
  genres?: string[];
}

// Curated demo books shown when the backend is unreachable, so discovery
// always remains useful (graceful degradation, same as the Dashboard).
const FALLBACK_BOOKS: Book[] = [
  {
    id: 'demo-1',
    title: 'The Midnight Library',
    authors: 'Matt Haig',
    cover_url: '',
    rating: 4.3,
    genres: ['Fiction'],
    published_year: 2020,
    description: 'Between life and death there is a library, and within that library, the shelves go on forever.'
  },
  {
    id: 'demo-2',
    title: 'Project Hail Mary',
    authors: 'Andy Weir',
    cover_url: '',
    rating: 4.7,
    genres: ['Sci-Fi'],
    published_year: 2021,
    description: 'A lone astronaut must save the earth from disaster in this near-perfect sci-fi thriller.'
  },
  {
    id: 'demo-3',
    title: 'Tomorrow, and Tomorrow, and Tomorrow',
    authors: 'Gabrielle Zevin',
    cover_url: '',
    rating: 4.5,
    genres: ['Fiction'],
    published_year: 2022,
    description: 'A decade-spanning story about friendship, creativity, and the worlds we build together.'
  },
  {
    id: 'demo-4',
    title: 'The House in the Cerulean Sea',
    authors: 'T.J. Klune',
    cover_url: '',
    rating: 4.6,
    genres: ['Fantasy'],
    published_year: 2020,
    description: 'A caseworker journeys to a remote island orphanage for magical children.'
  },
  {
    id: 'demo-5',
    title: 'Piranesi',
    authors: 'Susanna Clarke',
    cover_url: '',
    rating: 4.4,
    genres: ['Fantasy'],
    published_year: 2020,
    description: 'A man lives in an endless house of halls and statues, and the mystery of its world unfolds.'
  },
  {
    id: 'demo-6',
    title: 'A Psalm for the Wild-Built',
    authors: 'Becky Chambers',
    cover_url: '',
    rating: 4.4,
    genres: ['Sci-Fi'],
    published_year: 2021,
    description: 'A tea monk and a robot explore what it means to be alive in a gentle, hopeful novella.'
  }
];
// Main component
export const AIBookRecommendations: React.FC<RecommendationProps> = ({
  userId,
  limit = 20,
  strategy = 'hybrid',
  genres = []
}) => {
  const dispatch = useAppDispatch();
  const theme = useAppSelector((state) => state.dashboard.theme);
  const performanceMode = useAppSelector((state) => state.dashboard.performanceMode);

  // Read recommendations from the Redux store (source of truth)
  const storeRecommendations = useAppSelector((state) => state.books.recommendations);
  const storeLoading = useAppSelector((state) => state.books.loading);
  const storeError = useAppSelector((state) => state.books.error);

  // Personalization source: account + onboarding unlocks taste-based ranking
  const isAuthenticated = useAppSelector((state) => state.user.isAuthenticated);
  const hasCompletedOnboarding = useAppSelector(
    (state) => state.user.hasCompletedOnboarding
  );
  const userPreferences = useAppSelector((state) => state.user.preferences);

  /**
   * Chain-of-Thought: Rank the catalog against the reader's taste profile.
   * This runs locally and instantly — no backend round-trip required.
   */
  const personalizedPicks = useMemo(() => {
    if (!isAuthenticated || !hasCompletedOnboarding) return [] as Book[];
    return getPersonalizedRecommendations(userPreferences, { limit }).map((rec) => ({
      id: rec.book.id,
      title: rec.book.title,
      authors: rec.book.authors,
      cover_url: rec.book.cover_url,
      rating: rec.book.rating,
      genres: rec.book.genres,
      published_year: rec.book.published_year,
      description: rec.book.description,
      ai_recommendation_score: rec.score,
      ai_explanation: rec.reasons[0]
    }));
  }, [isAuthenticated, hasCompletedOnboarding, userPreferences, limit]);

  // Local mirror so the grid re-renders cheaply and we can track viewed items
  const [viewedRecommendations, setViewedRecommendations] = useState<Set<string>>(new Set());
  // When the backend is unreachable we show curated demo picks instead of a raw error
  const [showFallback, setShowFallback] = useState(false);

  /**
   * Chain-of-Thought: Fetch recommendations through the Redux thunk on mount.
   * The thunk handles caching, delta updates, and error normalization.
   */
  useEffect(() => {
    dispatch(setLoading(true));
    dispatch(
      fetchRecommendations({
        userId,
        limit,
        strategy,
        genres
      })
    );
  }, [dispatch, userId, limit, strategy, genres.join(',')]);

  /**
   * Chain-of-Thought: Track book interactions to improve recommendations
   * Memory: Store interactions in Redux for persistence across sessions
   */
  const handleBookClick = (book: Book) => {
    dispatch(addToRecentRecommendations(book));
    setViewedRecommendations((prev) => new Set([...prev, book.id]));
  };

  /**
   * Chain-of-Thought: Responsive column count for the book grid.
   * Time Complexity: O(1) computation per render.
   */
  const columnCount = useMemo(() => {
    if (typeof window === 'undefined') return 4;
    const width = window.innerWidth;
    if (width < 640) return 2;
    if (width < 1024) return 3;
    return 4;
  }, []);

  // Error state (prefer store error, fall back to local) — skipped when
  // personalized picks are already available.
  const displayError = storeError ?? null;
  if (personalizedPicks.length === 0 && displayError && !showFallback) {
    // Graceful degradation: offer curated demo picks instead of a dead end.
    return (
      <div className="recommendations-fallback">
        <ErrorMessage
          message="Could not reach the recommendation engine."
          details="You can retry, or browse curated picks while the service is offline."
          onRetry={() => {
            dispatch(setError(null));
            dispatch(fetchRecommendations({ userId, limit, strategy, genres }));
          }}
          onDismiss={() => setShowFallback(true)}
        />
      </div>
    );
  }

  // Loading state (skip when already showing fallback or personalized picks)
  if (
    personalizedPicks.length === 0 &&
    !showFallback &&
    (storeLoading || (storeRecommendations.length === 0 && !storeError))
  ) {
    return <LoadingSpinner message="Finding your perfect reads..." />;
  }

  // Empty state (only when not in fallback mode and no personalized picks)
  if (personalizedPicks.length === 0 && storeRecommendations.length === 0 && !showFallback) {
    return (
      <div className="ai-book-recommendations">
        <h2 className="recommendations-title">AI-Powered Book Recommendations</h2>
        <p className="recommendation-empty">
          No recommendations yet. Adjust your filters or add books to your shelf to get
          personalized picks.
        </p>
      </div>
    );
  }

  /**
   * Chain-of-Thought: Responsive CSS grid — avoids an uninstalled virtualization
   * dependency while keeping DOM size manageable for typical result sets.
   */
  const booksToRender =
    personalizedPicks.length > 0
      ? personalizedPicks
      : showFallback && storeRecommendations.length === 0
        ? FALLBACK_BOOKS
        : (storeRecommendations as unknown as Book[]);

  return (
    <div className={`ai-book-recommendations theme-${theme} performance-${performanceMode}`}>
      <div className="flex items-center gap-2">
        <h2 className="recommendations-title">AI-Powered Book Recommendations</h2>
        {personalizedPicks.length > 0 && (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
            ✨ Personalized for you
          </span>
        )}
      </div>

      {showFallback && storeRecommendations.length === 0 && (
        <p className="recommendation-fallback-note">
          Showing curated picks while the recommendation service is offline.{' '}
          <button
            className="text-blue-600 dark:text-blue-400 underline"
            onClick={() => {
              setShowFallback(false);
              dispatch(fetchRecommendations({ userId, limit, strategy, genres }));
            }}
          >
            Retry
          </button>
        </p>
      )}

      <div
        className="recommendations-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${columnCount}, minmax(0, 1fr))`,
          gap: '1.5rem',
          padding: '1rem 0'
        }}
      >
        {booksToRender.map((book) => (
          <div key={book.id} className="book-grid-cell">
            <BookCard
              book={book}
              isNew={!viewedRecommendations.has(book.id)}
              onClick={() => handleBookClick(book)}
            />
          </div>
        ))}
      </div>

      <div className="recommendations-footer">
        <p className="recommendation-explanation">
          These recommendations are powered by our hybrid AI engine, which analyzes reading
          patterns, book characteristics, and community reviews.
        </p>
      </div>
    </div>
  );
};

export default AIBookRecommendations;
