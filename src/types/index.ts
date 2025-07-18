// Frontend TypeScript Bootstrap Template
// File: src/types/index.ts

export interface Book {
  id: string;
  title: string;
  author: string;
  isbn?: string;
  genre: string[];
  rating: number;
  description: string;
  publishedDate: Date;
  coverUrl?: string;
  relevanceScore?: number;
}

export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  url: string;
  publishedAt: Date;
  source: string;
  category: string;
  isExpanded?: boolean;
  facts?: FactCheck[];
  bookRecommendations?: Book[];
}

export interface FactCheck {
  claim: string;
  verified: boolean;
  source: string;
  confidence: number;
  explanation?: string;
}

export interface UserPreferences {
  favoriteGenres: string[];
  readingGoals: number;
  notificationSettings: {
    email: boolean;
    push: boolean;
    newsletter: boolean;
  };
}

export interface APIResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  timestamp: Date;
}

// Error types
export class AppError extends Error {
  constructor(
    public code: string,
    message: string,
    public statusCode: number = 500
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class ValidationError extends AppError {
  constructor(message: string) {
    super('VALIDATION_ERROR', message, 400);
  }
}

export class NetworkError extends AppError {
  constructor(message: string) {
    super('NETWORK_ERROR', message, 503);
  }
}
