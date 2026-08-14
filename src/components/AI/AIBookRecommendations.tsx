/**
 * 📚 AI Book Recommendations Component
 * Chain-of-Thought: Fetch personalized recommendations through Redux and render
 * them in a responsive grid with loading / error / empty states.
 * Memory: Track viewed recommendations to mark new items
 * Forward-Thinking: Strategy and genre filters plug directly into the backend
 */

import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import {
  addToRecentRecommendations,
  fetchRecommendations,
  setError,
  setLoading
} from '../../stores/books/booksSlice';
import { bentoPlacement } from '../../utils/bento';
import { matchesGenre } from '../../utils/bookFilters';
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
  ratingsCount?: number;
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
  /** Client-side genre filter (alias-aware) applied on top of whatever the
   * API returned — keeps Discover's genre chips consistent sitewide. */
  filterGenres?: string[];
}

// Main component
export const AIBookRecommendations: React.FC<RecommendationProps> = ({
  userId,
  limit = 20,
  strategy = 'hybrid',
  genres = [],
  filterGenres = []
}) => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
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
      ratingsCount: rec.book.ratingsCount,
      genres: rec.book.genres,
      published_year: rec.book.published_year,
      description: rec.book.description,
      ai_recommendation_score: rec.score,
      ai_explanation: rec.reasons[0]
    }));
  }, [isAuthenticated, hasCompletedOnboarding, userPreferences, limit]);

  // Local mirror so the grid re-renders cheaply and we can track viewed items
  const [viewedRecommendations, setViewedRecommendations] = useState<Set<string>>(new Set());
  // When the backend is unreachable we show an honest error with retry.

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
   * Chain-of-Thought: Track book interactions to improve recommendations.
   * Every card opens its shareable /book/:id detail page (which auto-fetches
   * the full record for external ids), so discovery always ends in action.
   */
  const handleBookClick = (book: Book) => {
    dispatch(addToRecentRecommendations(book));
    setViewedRecommendations((prev) => new Set([...prev, book.id]));
    navigate(`/book/${encodeURIComponent(book.id)}`);
  };

  // Error state (prefer store error, fall back to local) — skipped when
  // personalized picks are already available.
  const displayError = storeError ?? null;
  if (personalizedPicks.length === 0 && displayError) {
    return (
      <div className="recommendations-fallback">
        <ErrorMessage
          message="Could not reach the recommendation engine."
          details="Check your connection and try again — your picks are ready as soon as the service is back."
          onRetry={() => {
            dispatch(setError(null));
            dispatch(fetchRecommendations({ userId, limit, strategy, genres }));
          }}
        />
      </div>
    );
  }

  // Loading state (skip when personalized picks are already available)
  if (
    personalizedPicks.length === 0 &&
    (storeLoading || (storeRecommendations.length === 0 && !storeError))
  ) {
    return <LoadingSpinner message="Finding your perfect reads..." />;
  }

  // Empty state
  if (personalizedPicks.length === 0 && storeRecommendations.length === 0) {
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
  const booksToRender = (
    personalizedPicks.length > 0
      ? personalizedPicks
      : (storeRecommendations as unknown as Book[])
  ).filter(
    (b) => filterGenres.length === 0 || matchesGenre(b.genres, filterGenres[0])
  );

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

      <div className="bento-grid">
        {booksToRender.map((book, index) => {
          const placement = bentoPlacement(index)
          return (
            <div key={book.id} className={`bento-item ${placement.className}`}>
              <BookCard
                book={book}
                variant={placement.featured ? 'featured' : 'standard'}
                isNew={!viewedRecommendations.has(book.id)}
                onClick={() => handleBookClick(book)}
              />
            </div>
          )
        })}
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
