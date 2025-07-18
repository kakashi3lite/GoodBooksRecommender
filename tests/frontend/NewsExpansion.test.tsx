// React Component Test Template
// File: tests/frontend/NewsExpansion.test.tsx

import { configureStore } from '@reduxjs/toolkit';
import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { Provider } from 'react-redux';

import { NewsExpansion } from '../../src/components/NewsExpansion';
import { apiService } from '../../src/services/ApiService';
import { NewsItem } from '../../src/types';

// Mock API service
jest.mock('../../src/services/ApiService');
const mockApiService = apiService as jest.Mocked<typeof apiService>;

// Mock store
const mockStore = configureStore({
  reducer: {
    news: (state = { items: [], loading: false, error: null }, action) => state,
  },
});

const mockNewsItem: NewsItem = {
  id: 'news-1',
  title: 'Test News Title',
  summary: 'Test news summary',
  url: 'https://example.com/news/1',
  publishedAt: new Date('2025-07-17'),
  source: 'Test Source',
  category: 'Technology',
  isExpanded: false,
};

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <Provider store={mockStore}>
      {component}
    </Provider>
  );
};

describe('NewsExpansion Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders news item correctly', () => {
    renderWithProvider(<NewsExpansion newsItem={mockNewsItem} />);
    
    expect(screen.getByText('Test News Title')).toBeInTheDocument();
    expect(screen.getByText('Test news summary')).toBeInTheDocument();
    expect(screen.getByText('Test Source')).toBeInTheDocument();
  });

  test('expands news when expand button is clicked', async () => {
    const expandedNewsItem = {
      ...mockNewsItem,
      isExpanded: true,
      facts: [
        {
          claim: 'Test fact',
          verified: true,
          source: 'Wikipedia',
          confidence: 0.95,
        },
      ],
      bookRecommendations: [
        {
          id: 'book-1',
          title: 'Test Book',
          author: 'Test Author',
          genre: ['Technology'],
          rating: 4.5,
          description: 'Test book description',
          publishedDate: new Date('2025-01-01'),
        },
      ],
    };

    mockApiService.expandNews.mockResolvedValue(expandedNewsItem);

    renderWithProvider(<NewsExpansion newsItem={mockNewsItem} />);
    
    const expandButton = screen.getByRole('button', { name: /expand/i });
    fireEvent.click(expandButton);

    await waitFor(() => {
      expect(mockApiService.expandNews).toHaveBeenCalledWith('news-1');
    });

    await waitFor(() => {
      expect(screen.getByText('Test fact')).toBeInTheDocument();
      expect(screen.getByText('Test Book')).toBeInTheDocument();
    });
  });

  test('handles expansion error gracefully', async () => {
    mockApiService.expandNews.mockRejectedValue(new Error('Network error'));

    renderWithProvider(<NewsExpansion newsItem={mockNewsItem} />);
    
    const expandButton = screen.getByRole('button', { name: /expand/i });
    fireEvent.click(expandButton);

    await waitFor(() => {
      expect(screen.getByText(/error loading additional content/i)).toBeInTheDocument();
    });
  });

  test('displays loading state during expansion', async () => {
    let resolvePromise: (value: NewsItem) => void;
    const promise = new Promise<NewsItem>((resolve) => {
      resolvePromise = resolve;
    });
    
    mockApiService.expandNews.mockReturnValue(promise);

    renderWithProvider(<NewsExpansion newsItem={mockNewsItem} />);
    
    const expandButton = screen.getByRole('button', { name: /expand/i });
    fireEvent.click(expandButton);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    // Resolve promise to cleanup
    resolvePromise!({ ...mockNewsItem, isExpanded: true });
  });

  test('accessibility: has proper ARIA labels', () => {
    renderWithProvider(<NewsExpansion newsItem={mockNewsItem} />);
    
    const expandButton = screen.getByRole('button', { name: /expand/i });
    expect(expandButton).toHaveAttribute('aria-expanded', 'false');
    expect(expandButton).toHaveAttribute('aria-controls');
  });

  test('accessibility: supports keyboard navigation', () => {
    renderWithProvider(<NewsExpansion newsItem={mockNewsItem} />);
    
    const expandButton = screen.getByRole('button', { name: /expand/i });
    expandButton.focus();
    expect(expandButton).toHaveFocus();

    fireEvent.keyDown(expandButton, { key: 'Enter' });
    expect(mockApiService.expandNews).toHaveBeenCalled();
  });
});
