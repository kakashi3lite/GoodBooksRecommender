/**
 * 📚 AI Book Recommendations Component
 * Chain-of-Thought: Efficiently render book recommendations with virtualization for O(windowSize) complexity
 * Memory: Track interaction history to improve recommendations over time
 * Forward-Thinking: Support for different recommendation algorithms and strategies
 */

import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { API_ENDPOINTS } from '../../utils/api';
import { BookCard } from '../UI/BookCard';
import { LoadingSpinner } from '../UI/LoadingSpinner';
import { ErrorMessage } from '../UI/ErrorMessage';

// Type definitions
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

// Main component
export const AIBookRecommendations: React.FC<RecommendationProps> = ({
  userId,
  limit = 20,
  strategy = 'hybrid',
  genres = []
}) => {
  // Redux state
  const dispatch = useAppDispatch();
  const theme = useAppSelector(state => state.dashboard.theme);
  const performanceMode = useAppSelector(state => state.dashboard.performanceMode);
  
  // Local state for recommendations
  const [recommendations, setRecommendations] = useState<Book[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setErrorState] = useState<string | null>(null);
  
  // Memory: Track which recommendations the user has seen
  const [viewedRecommendations, setViewedRecommendations] = useState<Set<string>>(new Set());
  
  /**
   * Chain-of-Thought: Use a Web Worker for data preprocessing
   * This moves heavy computation off the main thread
   * Time Complexity: O(n) for processing, but non-blocking
   */
  const workerRef = React.useRef<Worker | null>(null);

  useEffect(() => {
    // Create Web Worker for background processing
    if (typeof window !== 'undefined' && window.Worker) {
      workerRef.current = new Worker(new URL('@utils/recommendation.worker.ts', import.meta.url));
      
      workerRef.current.onmessage = (event) => {
        if (event.data.type === 'PROCESSED_RECOMMENDATIONS') {
          setRecommendations(event.data.recommendations);
          setIsLoading(false);
        }
      };
      
      return () => {
        workerRef.current?.terminate();
      };
    }
  }, []);
  
  /**
   * Chain-of-Thought: Fetch recommendations with real data
   * Time Complexity: Network I/O is O(1), but response processing is O(n)
   */
  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        setIsLoading(true);
        dispatch(setLoading(true));
        
        // Construct query parameters
        const params = {
          user_id: userId,
          limit,
          strategy,
          genres: genres.join(',')
        };
        
        // Fetch from API
        const response = await axios.get(API_ENDPOINTS.books.recommend(), { params });
        
        // If we have a worker, send data for processing
        if (workerRef.current) {
          workerRef.current.postMessage({
            type: 'PROCESS_RECOMMENDATIONS',
            data: response.data
          });
        } else {
          // If no worker support, process on main thread
          setRecommendations(response.data);
          setIsLoading(false);
        }
        
        dispatch(setLoading(false));
      } catch (err) {
        console.error('Failed to fetch recommendations:', err);
        setErrorState(err instanceof Error ? err.message : 'Failed to load recommendations');
        dispatch(setError('Failed to load recommendations'));
        setIsLoading(false);
        dispatch(setLoading(false));
      }
    };
    
    fetchRecommendations();
  }, [dispatch, userId, limit, strategy, genres]);
  
  /**
   * Chain-of-Thought: Track book interactions to improve recommendations
   * Memory: Store interactions in Redux for persistence across sessions
   */
  const handleBookClick = (book: Book) => {
    // Add to recently viewed in Redux
    dispatch(addToRecentRecommendations(book));
    
    // Mark as viewed in local state
    setViewedRecommendations(prev => new Set([...prev, book.id]));
  };
  
  /**
   * Chain-of-Thought: Compute grid dimensions for virtualized list
   * This optimizes rendering for O(windowSize) complexity instead of O(n)
   */
  const gridConfig = useMemo(() => {
    // Default values for desktop
    let columnCount = 4;
    
    // Adjust for different screen sizes
    if (typeof window !== 'undefined') {
      const width = window.innerWidth;
      if (width < 640) columnCount = 2;
      else if (width < 1024) columnCount = 3;
    }
    
    return {
      columnCount,
      columnWidth: 250,
      rowHeight: 380,
    };
  }, []);
  
  // Error state
  if (error) {
    return <ErrorMessage message={error} onRetry={() => setErrorState(null)} />;
  }
  
  // Loading state
  if (isLoading) {
    return <LoadingSpinner message="Finding your perfect reads..." />;
  }
  
  /**
   * Chain-of-Thought: Use virtualization for efficient rendering
   * Time Complexity: O(windowSize) rendering instead of O(n)
   */
  return (
    <div className="ai-book-recommendations">
      <h2 className="recommendations-title">AI-Powered Book Recommendations</h2>
      
      <div className="recommendations-container" style={{ height: '800px', width: '100%' }}>
        <AutoSizer>
          {({ height, width }) => {
            const rowCount = Math.ceil(recommendations.length / gridConfig.columnCount);
            
            return (
              <FixedSizeGrid
                columnCount={gridConfig.columnCount}
                columnWidth={width / gridConfig.columnCount}
                height={height}
                rowCount={rowCount}
                rowHeight={gridConfig.rowHeight}
                width={width}
                itemData={{
                  recommendations,
                  columnCount: gridConfig.columnCount,
                  handleBookClick
                }}
              >
                {({ columnIndex, rowIndex, style, data }) => {
                  const index = rowIndex * data.columnCount + columnIndex;
                  const book = data.recommendations[index];
                  
                  if (!book) return null;
                  
                  return (
                    <div style={style} className="book-grid-cell">
                      <BookCard
                        book={book}
                        isNew={!viewedRecommendations.has(book.id)}
                        onClick={() => data.handleBookClick(book)}
                      />
                    </div>
                  );
                }}
              </FixedSizeGrid>
            );
          }}
        </AutoSizer>
      </div>
      
      <div className="recommendations-footer">
        <p className="recommendation-explanation">
          These recommendations are powered by our advanced AI system that analyzes reading patterns, book characteristics, and community reviews.
        </p>
      </div>
    </div>
  );
};

export default AIBookRecommendations;
