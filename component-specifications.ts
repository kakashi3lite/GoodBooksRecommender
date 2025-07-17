/**
 * 🎨 Production-Ready Component Specifications
 * Figma-to-Code Translation Layer
 * 
 * These TypeScript interfaces define the exact structure needed for 
 * automated component generation from Figma wireframes.
 */

// ===== CORE DATA TYPES =====

export interface BookData {
  id: string;
  title: string;
  author: string;
  coverUrl?: string;
  rating?: number;
  pageCount?: number;
  genres?: string[];
  publishedYear?: number;
  description?: string;
  isbn?: string;
  progress?: number; // 0-100 for reading progress
  matchScore?: number; // 0-100 for recommendation relevance
  aiExplanation?: string; // AI-generated recommendation reasoning
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  avatar?: string;
  preferences: UserPreferences;
  readingHistory: ReadingSession[];
  favoriteGenres: string[];
}

export interface ReadingSession {
  id: string;
  bookId: string;
  startTime: Date;
  endTime?: Date;
  pagesRead: number;
  sessionDuration: number; // minutes
  device: 'mobile' | 'desktop' | 'tablet' | 'e-reader';
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  brightness: number; // 0-100
  fontSize: number; // 12-24px
  fontFamily: 'serif' | 'sans' | 'mono';
  readingStyle: 'skim' | 'deep' | 'thematic';
  notifications: NotificationSettings;
  autoAdjustBrightness: boolean;
}

export interface NotificationSettings {
  newRecommendations: boolean;
  readingReminders: boolean;
  weeklyReports: boolean;
  friendActivity: boolean;
}

// ===== COMPONENT INTERFACES =====

/**
 * Dashboard Header Component
 * Fixed header with navigation, search, and user actions
 */
export interface DashboardHeaderProps {
  user: UserProfile;
  activeTab: NavigationTab;
  searchQuery: string;
  onTabChange: (tab: NavigationTab) => void;
  onSearch: (query: string) => void;
  onSettingsOpen: () => void;
  onUserMenuOpen: () => void;
  className?: string;
}

export type NavigationTab = 'library' | 'recommendations' | 'analytics' | 'discover' | 'news';

/**
 * Book Card Component
 * Flexible card for displaying books in different contexts
 */
export interface BookCardProps {
  book: BookData;
  variant: BookCardVariant;
  size?: 'compact' | 'standard' | 'detailed';
  showProgress?: boolean;
  showMatchScore?: boolean;
  showAIExplanation?: boolean;
  onAction: (action: BookAction, book: BookData) => Promise<void>;
  className?: string;
  isLoading?: boolean;
}

export type BookCardVariant = 'library' | 'recommendation' | 'reading' | 'search';
export type BookAction = 'add' | 'start' | 'continue' | 'remove' | 'details' | 'preview';

export interface BookCardState {
  isHovered: boolean;
  actionInProgress: BookAction | null;
  loadingProgress: number;
}

/**
 * Settings Panel Component
 * Slide-in panel for user preferences
 */
export interface SettingsPanelProps {
  isOpen: boolean;
  settings: UserPreferences;
  onClose: () => void;
  onSettingsChange: (settings: Partial<UserPreferences>) => void;
  onSave: () => Promise<void>;
  onReset: () => void;
  autoSave?: boolean;
  className?: string;
}

/**
 * Smart Search Component
 * AI-powered search with intent analysis
 */
export interface SmartSearchProps {
  query: string;
  onQueryChange: (query: string) => void;
  onSearch: (query: string, filters?: SearchFilters) => void;
  isLoading?: boolean;
  intentAnalysis?: SearchIntent;
  suggestedFilters?: FilterTag[];
  results?: SearchResult[];
  placeholder?: string;
  enableAI?: boolean;
  className?: string;
}

export interface SearchIntent {
  topics: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  format: 'fiction' | 'non-fiction' | 'any';
  length: 'short' | 'medium' | 'long' | 'any';
  confidence: number; // 0-1
}

export interface SearchFilters {
  genres?: string[];
  authors?: string[];
  yearRange?: [number, number];
  ratingMin?: number;
  pageCountRange?: [number, number];
  matchScoreMin?: number;
}

export interface FilterTag {
  id: string;
  label: string;
  type: 'genre' | 'author' | 'difficulty' | 'format';
  icon?: string;
  isActive?: boolean;
}

export interface SearchResult {
  book: BookData;
  relevanceScore: number;
  aiExplanation: string;
  highlightedTerms: string[];
}

/**
 * Sidebar Navigation Component
 * Collapsible sidebar with library sections and smart lists
 */
export interface SidebarNavigationProps {
  activeSection: SidebarSection;
  onSectionChange: (section: SidebarSection) => void;
  libraryStats: LibraryStats;
  smartLists: SmartList[];
  isCollapsed?: boolean;
  onToggleCollapse: () => void;
  className?: string;
}

export type SidebarSection = 'reading' | 'want-to-read' | 'completed' | 'favorites' | 'trending' | 'similar' | 'top-rated' | 'new-releases';

export interface LibraryStats {
  reading: number;
  wantToRead: number;
  completed: number;
  favorites: number;
}

export interface SmartList {
  id: string;
  name: string;
  icon: string;
  count: number;
  type: 'dynamic' | 'static';
  description?: string;
}

/**
 * Book Grid Component
 * Virtualized grid for displaying large collections
 */
export interface BookGridProps {
  books: BookData[];
  variant: BookCardVariant;
  loading?: boolean;
  error?: string;
  onLoadMore?: () => void;
  onBookAction: (action: BookAction, book: BookData) => Promise<void>;
  filters?: SearchFilters;
  sortBy?: SortOption;
  viewMode?: 'grid' | 'list';
  className?: string;
}

export type SortOption = 'relevance' | 'title' | 'author' | 'rating' | 'year' | 'pages' | 'added';

/**
 * Reading Analytics Component
 * Dashboard for reading statistics and insights
 */
export interface ReadingAnalyticsProps {
  timeRange: TimeRange;
  onTimeRangeChange: (range: TimeRange) => void;
  stats: ReadingStats;
  insights: PersonalizedInsight[];
  charts: ChartData[];
  className?: string;
}

export type TimeRange = '7d' | '30d' | '90d' | '1y' | 'all';

export interface ReadingStats {
  booksRead: number;
  pagesRead: number;
  readingTime: number; // minutes
  goalProgress: number; // 0-100
  trends: {
    books: number; // change vs previous period
    pages: number;
    time: number;
  };
}

export interface PersonalizedInsight {
  id: string;
  type: 'pattern' | 'recommendation' | 'achievement';
  icon: string;
  title: string;
  description: string;
  actionable: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface ChartData {
  id: string;
  title: string;
  type: 'line' | 'bar' | 'pie' | 'doughnut';
  data: any; // Chart.js compatible data
  options?: any; // Chart.js options
}

// ===== HOOK INTERFACES =====

/**
 * useBooks Hook
 * State management for book collections
 */
export interface UseBooksReturn {
  books: BookData[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  hasMore: boolean;
  
  // Actions
  fetchBooks: (filters?: SearchFilters) => Promise<void>;
  searchBooks: (query: string, filters?: SearchFilters) => Promise<void>;
  addBook: (book: BookData) => Promise<void>;
  removeBook: (bookId: string) => Promise<void>;
  updateBook: (bookId: string, updates: Partial<BookData>) => Promise<void>;
  loadMore: () => Promise<void>;
  
  // Utilities
  getBookById: (id: string) => BookData | undefined;
  clearSearch: () => void;
  refetch: () => Promise<void>;
}

/**
 * useSettings Hook
 * User preferences management
 */
export interface UseSettingsReturn {
  settings: UserPreferences;
  loading: boolean;
  error: string | null;
  isDirty: boolean;
  
  // Actions
  updateSettings: (updates: Partial<UserPreferences>) => void;
  saveSettings: () => Promise<void>;
  resetSettings: () => void;
  
  // Theme utilities
  applyTheme: (theme: 'light' | 'dark' | 'auto') => void;
  adjustBrightness: (brightness: number) => void;
  
  // Auto-save
  enableAutoSave: () => void;
  disableAutoSave: () => void;
}

/**
 * useSearch Hook
 * AI-powered search functionality
 */
export interface UseSearchReturn {
  query: string;
  results: SearchResult[];
  intentAnalysis: SearchIntent | null;
  suggestedFilters: FilterTag[];
  loading: boolean;
  error: string | null;
  
  // Actions
  setQuery: (query: string) => void;
  search: (query?: string, filters?: SearchFilters) => Promise<void>;
  applyFilter: (filter: FilterTag) => void;
  removeFilter: (filterId: string) => void;
  clearFilters: () => void;
  clearSearch: () => void;
  
  // AI features
  analyzeIntent: (query: string) => Promise<SearchIntent>;
  generateSuggestions: (query: string) => Promise<FilterTag[]>;
}

// ===== UTILITY TYPES =====

export interface ComponentTheme {
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    success: string;
    warning: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  typography: {
    fontFamily: string;
    fontSize: string;
    lineHeight: string;
    fontWeight: string;
  };
  borderRadius: string;
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}

export interface AnimationConfig {
  duration: number;
  easing: string;
  delay?: number;
  fillMode?: 'forwards' | 'backwards' | 'both' | 'none';
}

export interface AccessibilityProps {
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  'aria-expanded'?: boolean;
  'aria-selected'?: boolean;
  'aria-checked'?: boolean;
  'aria-disabled'?: boolean;
  'aria-hidden'?: boolean;
  role?: string;
  tabIndex?: number;
}

// ===== PERFORMANCE TYPES =====

export interface VirtualizationConfig {
  itemHeight: number | ((index: number) => number);
  overscan: number;
  threshold: number;
  useIsScrolling: boolean;
}

export interface LazyLoadingConfig {
  threshold: number;
  rootMargin: string;
  triggerOnce: boolean;
  placeholder: React.ReactNode;
}

// ===== EVENT TYPES =====

export interface BookCardEvent {
  type: BookAction;
  book: BookData;
  timestamp: number;
  source: 'user' | 'system';
}

export interface SearchEvent {
  type: 'query' | 'filter' | 'result-click';
  query?: string;
  filter?: FilterTag;
  result?: SearchResult;
  timestamp: number;
}

export interface SettingsEvent {
  type: 'change' | 'save' | 'reset';
  setting: keyof UserPreferences;
  oldValue: any;
  newValue: any;
  timestamp: number;
}

// ===== CURSOR/VS CODE PROMPT TEMPLATES =====

export const COMPONENT_GENERATION_PROMPTS = {
  DASHBOARD_HEADER: `
    Generate a React TypeScript component for DashboardHeader using the provided interface.
    Requirements:
    - Fixed header with backdrop blur
    - Responsive navigation that collapses on mobile
    - Debounced search with intent analysis
    - Smooth tab transitions with underline animation
    - Settings panel trigger
    - Use CSS modules for styling
    - Full accessibility support
    - Performance optimized with React.memo
  `,
  
  BOOK_CARD: `
    Create a flexible BookCard component supporting multiple variants.
    Requirements:
    - Lazy-loaded cover images with shimmer placeholder
    - Hover animations with scale and shadow effects
    - Loading states for async actions
    - Progress bar for reading books
    - Match score display for recommendations
    - AI explanation with truncation
    - Action buttons with loading indicators
    - Keyboard navigation support
    - Optimistic UI updates
  `,
  
  SETTINGS_PANEL: `
    Build a slide-in SettingsPanel with real-time preview.
    Requirements:
    - Smooth slide animation from right
    - Real-time theme and brightness preview
    - Auto-save with debouncing
    - Form validation and error handling
    - Keyboard shortcuts (Escape to close)
    - Focus management and trap
    - Responsive layout for mobile
    - Undo/redo functionality
  `,
  
  SMART_SEARCH: `
    Implement AI-powered SmartSearch with intent analysis.
    Requirements:
    - Natural language input with auto-resize
    - Real-time intent analysis with visual feedback
    - Dynamic filter tag generation
    - Ranked results with AI explanations
    - Search history and suggestions
    - Voice input support
    - Advanced filtering options
    - Infinite scroll for results
  `
};

export default {
  // Export prompt templates for code generation
  COMPONENT_GENERATION_PROMPTS
};
