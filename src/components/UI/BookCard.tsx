/**
 * 📚 Book Card Component
 * Chain-of-Thought: Efficient rendering of book information with hover effects
 * Memory: Track interaction state for animations
 * Forward-Thinking: Support for different card layouts
 */

import { motion } from 'framer-motion';
import { Share2 } from 'lucide-react';
import React, { useState } from 'react';
import toast from 'react-hot-toast';
import BookCover from './BookCover';

interface Book {
  id: string;
  title: string;
  authors: string;
  cover_url: string;
  rating: number;
  genres?: string[];
  published_year?: number;
  description?: string;
  ai_recommendation_score?: number;
  ai_explanation?: string;
}

interface BookCardProps {
  book: Book;
  isNew?: boolean;
  onClick?: () => void;
  /** 'featured' renders a larger card with the description always visible (bento grid). */
  variant?: 'standard' | 'featured';
}

export const BookCard: React.FC<BookCardProps> = ({
  book,
  isNew = false,
  onClick,
  variant = 'standard'
}) => {
  // Local state for interaction tracking
  const [isHovered, setIsHovered] = useState(false);
  /**
   * Chain-of-Thought: every card can expand a short description inline — this
   * is the mobile-friendly way to read a blurb (hover panels don't exist on
   * touch screens). Featured cards keep the blurb open by default.
   */
  const [expanded, setIsExpanded] = useState(variant === 'featured');

  const toggleExpanded = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded((v) => !v);
  };

  /**
   * Chain-of-Thought: Generate star rating display
   * Time Complexity: O(1) computation
   */
  const renderRating = () => {
    const fullStars = Math.floor(book.rating);
    const halfStar = book.rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);

    return (
      <div className="book-rating" aria-label={`Rating: ${book.rating} out of 5 stars`}>
        {[...Array(fullStars)].map((_, i) => (
          <span key={`full-${i}`} className="star full-star">★</span>
        ))}
        {halfStar && <span className="star half-star">⯨</span>}
        {[...Array(emptyStars)].map((_, i) => (
          <span key={`empty-${i}`} className="star empty-star">☆</span>
        ))}
      </div>
    );
  };

  /**
   * Chain-of-Thought: Animate card with GPU-accelerated properties
   * Time Complexity: O(1) animation state change
   */
  const cardVariants = {
    initial: {
      scale: 1,
      y: 0,
      rotateY: 0
    },
    hover: {
      scale: 1.02,
      y: -5,
      rotateY: 3,
      transition: { duration: 0.3, ease: "easeOut" }
    }
  };

  /**
   * Chain-of-Thought: Copy this book's shareable URL without bubbling into
   * the card's own click handler (which navigates to the detail page).
   * Uses the native share sheet on mobile when available, clipboard otherwise.
   */
  const handleShare = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const url = `${window.location.origin}/book/${encodeURIComponent(book.id)}`;
    try {
      if (navigator.share) {
        await navigator.share({
          title: book.title,
          text: `Check out "${book.title}" by ${book.authors} on GoodBooks`,
          url
        });
        return;
      }
    } catch {
      // user dismissed the native sheet — fall through to clipboard copy
    }
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = url;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    toast.success('Link copied — anyone can open it 📎');
  };

  return (
    <motion.div
      className={`book-card ${isNew ? 'new-book' : ''} ${variant === 'featured' ? 'book-card-featured' : ''}`}
      variants={cardVariants}
      initial="initial"
      animate={isHovered ? "hover" : "initial"}
      whileTap={{ scale: 0.98 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={onClick}
      style={{
        perspective: "1000px"
      }}
    >
      {/* Share button — copies the book's shareable URL */}
      <button
        type="button"
        onClick={handleShare}
        aria-label={`Share ${book.title}`}
        className="absolute top-2 right-2 z-10 p-2.5 rounded-full bg-white/85 dark:bg-gray-800/85 backdrop-blur text-gray-500 dark:text-gray-300 shadow-md hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
      >
        <Share2 className="w-4 h-4" />
      </button>
      {/* New badge */}
      {isNew && (
        <motion.div
          className="new-badge"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring" }}
        >
          New
        </motion.div>
      )}

      {/* Book cover — generated art by default, real image when available */}
      <div className="book-cover-container">
        <BookCover
          title={book.title}
          author={book.authors}
          coverUrl={book.cover_url}
          genres={book.genres}
          seed={book.id}
          size="md"
          rounded="md"
        />
      </div>

      {/* Book info */}
      <h3 className="book-title" title={book.title}>
        {book.title}
      </h3>

      <p className="book-author" title={book.authors}>
        {book.authors}
      </p>

      {/* Rating stars */}
      {renderRating()}

      {/* Short description — expandable on every card (mobile friendly) */}
      {book.description && (
        <>
          <button
            type="button"
            onClick={toggleExpanded}
            aria-expanded={expanded}
            className="book-expand-toggle"
          >
            {expanded ? 'Hide description' : 'Show description'}
          </button>
          {expanded && <p className="book-expanded-desc">{book.description}</p>}
        </>
      )}

      {/* AI recommendation score */}
      {book.ai_recommendation_score !== undefined && (
        <div className="ai-score" title="AI recommendation score">
          <div
            className="ai-score-fill"
            style={{ width: `${Math.round(book.ai_recommendation_score * 100)}%` }}
          />
          <span className="ai-score-label">
            {Math.round(book.ai_recommendation_score * 100)}%
          </span>
        </div>
      )}

      {/* Hover info panel */}
      <motion.div
        className="book-info-panel"
        initial={{ opacity: 0 }}
        animate={{ opacity: isHovered ? 1 : 0 }}
      >
        {!expanded && book.description && (
          <p className="book-description">
            {book.description.length > 120
              ? `${book.description.substring(0, 120)}...`
              : book.description}
          </p>
        )}

        {book.ai_explanation && (
          <div className="ai-explanation">
            <span className="ai-badge">AI</span>
            <p>{book.ai_explanation}</p>
          </div>
        )}

        <div className="book-genres">
          {book.genres?.slice(0, 3).map(genre => (
            <span key={genre} className="book-genre-tag">
              {genre}
            </span>
          ))}
        </div>

        {book.published_year && (
          <p className="book-year">{book.published_year}</p>
        )}
      </motion.div>
    </motion.div>
  );
};

export default BookCard;
