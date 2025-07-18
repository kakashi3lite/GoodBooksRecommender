// API Service Layer Template
// File: src/services/ApiService.ts

import { APIResponse, Book, NetworkError, NewsItem, UserPreferences } from '../types';

class ApiService {
  private baseUrl: string;
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<APIResponse<T>> {
    const cacheKey = `${endpoint}-${JSON.stringify(options)}`;
    
    // Check cache first
    if (options.method === 'GET' || !options.method) {
      const cached = this.cache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
        return cached.data;
      }
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new NetworkError(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Cache successful GET requests
      if (options.method === 'GET' || !options.method) {
        this.cache.set(cacheKey, { data, timestamp: Date.now() });
      }

      return data;
    } catch (error) {
      if (error instanceof NetworkError) throw error;
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      throw new NetworkError(`Network request failed: ${errorMessage}`);
    }
  }

  // News API methods
  async getNews(): Promise<NewsItem[]> {
    const response = await this.request<NewsItem[]>('/news');
    return response.data;
  }

  async expandNews(newsId: string): Promise<NewsItem> {
    const response = await this.request<NewsItem>(`/news/${newsId}/expand`, {
      method: 'POST',
    });
    return response.data;
  }

  // Book recommendation methods
  async getRecommendations(preferences?: UserPreferences): Promise<Book[]> {
    const response = await this.request<Book[]>('/recommendations', {
      method: 'POST',
      body: JSON.stringify(preferences),
    });
    return response.data;
  }

  async getBooksByTopic(topic: string): Promise<Book[]> {
    const response = await this.request<Book[]>(`/books/topic/${encodeURIComponent(topic)}`);
    return response.data;
  }

  // User preferences
  async getUserPreferences(): Promise<UserPreferences> {
    const response = await this.request<UserPreferences>('/user/preferences');
    return response.data;
  }

  async updateUserPreferences(preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    const response = await this.request<UserPreferences>('/user/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
    return response.data;
  }

  // Utility methods
  clearCache(): void {
    this.cache.clear();
  }

  getCacheSize(): number {
    return this.cache.size;
  }
}

export const apiService = new ApiService();
export default ApiService;
