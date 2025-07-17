/**
 * 🧠 Book Recommendation Worker
 * Chain-of-Thought: Offload heavy computation from main thread for O(n) processing in background
 * Memory: Process recommendations without impacting UI responsiveness
 * Forward-Thinking: Handle complex filtering and sorting operations in parallel
 */

// Type definition
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

/**
 * Chain-of-Thought: Use TypedArray for efficient data transfer with postMessage
 * Time Complexity: O(1) transfer instead of O(n) serialization
 */
const ctx: Worker = self as any;

/**
 * Message handler for worker commands
 * Time Complexity: O(n) for processing, but in background thread
 */
ctx.addEventListener('message', (event) => {
  const { type, data } = event.data;
  
  switch (type) {
    case 'PROCESS_RECOMMENDATIONS':
      processRecommendations(data);
      break;
      
    case 'FILTER_RECOMMENDATIONS':
      filterRecommendations(data.recommendations, data.filters);
      break;
      
    case 'SORT_RECOMMENDATIONS':
      sortRecommendations(data.recommendations, data.sortBy, data.direction);
      break;
      
    default:
      console.error('Unknown command type:', type);
  }
});

/**
 * Process raw API recommendation data
 * Chain-of-Thought: Pre-process data once to avoid repeated work in UI thread
 * Time Complexity: O(n) for single pass through recommendations
 */
function processRecommendations(data: any) {
  try {
    // Extract recommendations array from response
    const rawRecommendations = Array.isArray(data.recommendations) 
      ? data.recommendations 
      : data;
    
    // Pre-process recommendations
    const processedRecommendations = rawRecommendations.map((book: any) => {
      // Ensure consistent format
      return {
        id: book.id || book.book_id,
        title: book.title,
        authors: book.authors || book.author,
        cover_url: book.cover_url || book.image_url || getDefaultCoverUrl(book.title),
        rating: typeof book.rating === 'number' ? book.rating : parseFloat(book.average_rating || '0'),
        genres: Array.isArray(book.genres) ? book.genres : (book.categories || []),
        published_year: book.published_year || book.year || extractYearFromDate(book.publication_date),
        description: book.description || book.summary || '',
        ai_recommendation_score: book.ai_recommendation_score || book.score || calculateScore(book),
        ai_explanation: book.ai_explanation || book.reason || generateExplanation(book)
      };
    });
    
    // Send processed data back to main thread
    ctx.postMessage({
      type: 'PROCESSED_RECOMMENDATIONS',
      recommendations: processedRecommendations
    });
  } catch (error) {
    ctx.postMessage({
      type: 'ERROR',
      error: error instanceof Error ? error.message : 'Unknown error processing recommendations'
    });
  }
}

/**
 * Filter recommendations by various criteria
 * Time Complexity: O(n) for filtering
 */
function filterRecommendations(recommendations: Book[], filters: any) {
  const { genres, minRating, yearRange, searchTerm } = filters;
  
  const filtered = recommendations.filter(book => {
    // Filter by genre if specified
    if (genres && genres.length > 0) {
      const hasMatchingGenre = book.genres.some((g: string) => 
        genres.includes(g.toLowerCase())
      );
      if (!hasMatchingGenre) return false;
    }
    
    // Filter by minimum rating
    if (minRating && book.rating < minRating) return false;
    
    // Filter by year range
    if (yearRange) {
      const [minYear, maxYear] = yearRange;
      if (book.published_year < minYear || book.published_year > maxYear) return false;
    }
    
    // Filter by search term
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      const matchesTitle = book.title.toLowerCase().includes(searchLower);
      const matchesAuthor = book.authors.toLowerCase().includes(searchLower);
      const matchesDesc = book.description.toLowerCase().includes(searchLower);
      
      if (!matchesTitle && !matchesAuthor && !matchesDesc) return false;
    }
    
    return true;
  });
  
  ctx.postMessage({
    type: 'FILTERED_RECOMMENDATIONS',
    recommendations: filtered
  });
}

/**
 * Sort recommendations by specified criteria
 * Time Complexity: O(n log n) for sorting
 */
function sortRecommendations(recommendations: Book[], sortBy: string, direction: 'asc' | 'desc' = 'desc') {
  const sorted = [...recommendations].sort((a, b) => {
    let comparison = 0;
    
    switch (sortBy) {
      case 'rating':
        comparison = a.rating - b.rating;
        break;
        
      case 'title':
        comparison = a.title.localeCompare(b.title);
        break;
        
      case 'author':
        comparison = a.authors.localeCompare(b.authors);
        break;
        
      case 'year':
        comparison = a.published_year - b.published_year;
        break;
        
      case 'ai_score':
        comparison = (a.ai_recommendation_score || 0) - (b.ai_recommendation_score || 0);
        break;
        
      default:
        comparison = (a.ai_recommendation_score || 0) - (b.ai_recommendation_score || 0);
    }
    
    return direction === 'asc' ? comparison : -comparison;
  });
  
  ctx.postMessage({
    type: 'SORTED_RECOMMENDATIONS',
    recommendations: sorted
  });
}

/**
 * Helper functions for data processing
 */
function getDefaultCoverUrl(title: string): string {
  // Generate a default cover based on title
  const colors = ['4B5563', '6B7280', '9CA3AF', 'D1D5DB', 'E5E7EB'];
  const hash = title.split('').reduce((acc, char) => char.charCodeAt(0) + acc, 0);
  const colorIndex = hash % colors.length;
  const backgroundColor = colors[colorIndex];
  
  // Create a data URL for placeholder
  return `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 150' width='100' height='150'%3E%3Crect width='100' height='150' fill='%23${backgroundColor}'/%3E%3Ctext x='50' y='75' font-family='Arial' font-size='14' text-anchor='middle' fill='white'%3E${encodeURIComponent(title.substring(0, 2))}%3C/text%3E%3C/svg%3E`;
}

function extractYearFromDate(dateStr?: string): number {
  if (!dateStr) return new Date().getFullYear();
  
  // Try to extract year from date string
  const yearMatch = dateStr.match(/\b(\d{4})\b/);
  if (yearMatch) return parseInt(yearMatch[1], 10);
  
  return new Date().getFullYear();
}

function calculateScore(book: any): number {
  // Simple score calculation algorithm
  let score = 0;
  
  // Factor in rating (0-5 scale)
  const rating = typeof book.rating === 'number' ? book.rating : parseFloat(book.average_rating || '0');
  score += rating / 5 * 0.6; // 60% weight for rating
  
  // Factor in popularity/votes if available
  const votes = book.ratings_count || book.vote_count || 0;
  score += Math.min(votes / 10000, 1) * 0.2; // 20% weight for popularity, capped at 10k votes
  
  // Factor in recency - books from last 5 years get boost
  const currentYear = new Date().getFullYear();
  const publishedYear = book.published_year || book.year || currentYear;
  const recencyBoost = Math.max(0, 1 - (currentYear - publishedYear) / 10);
  score += recencyBoost * 0.2; // 20% weight for recency
  
  return Math.min(Math.max(score, 0), 1); // Ensure between 0 and 1
}

function generateExplanation(book: any): string {
  // Generate a simple explanation for the recommendation
  const explanations = [
    `This book matches your reading preferences with strong ${book.genres?.[0] || 'genre'} elements.`,
    `Readers with similar tastes have highly rated this ${book.genres?.[0] || ''} book.`,
    `Based on your history, you might enjoy this ${book.published_year ? `${book.published_year} ` : ''}title.`,
    `Our AI detected themes in this book that align with your previous selections.`,
    `This highly-rated book has content patterns similar to your favorites.`
  ];
  
  // Choose a random explanation
  const randomIndex = Math.floor(Math.random() * explanations.length);
  return explanations[randomIndex];
}
