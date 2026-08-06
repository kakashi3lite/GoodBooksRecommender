/**
 * 📚 Book Card Component
 * Chain-of-Thought: Efficient rendering of book information with hover effects
 * Memory: Track interaction state for animations
 * Forward-Thinking: Support for different card layouts
 */

import { motion } from 'framer-motion';
import React, { useState } from 'react';
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
}

export const BookCard: React.FC<BookCardProps> = ({
  book,
  isNew = false,
  onClick
}) => {
  // Local state for interaction tracking
  const [isHovered, setIsHovered] = useState(false);

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

  return (
    <motion.div
      className={`book-card ${isNew ? 'new-book' : ''}`}
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
        {book.description && (
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
