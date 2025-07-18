# 🤖 Superhuman AI Integration Prompt

## 🔄 Python-to-TypeScript AI Bridge Implementation

I need you to create adapter code to connect the React frontend with the Python AI engine components. This is a critical part of fixing our dashboard UI issues.

## 🧩 Components Needing Integration

1. `src/news/ai/elearnfit_optimizer.py` → TypeScript integration
2. `src/news/ai/scorerag_summarization.py` → TypeScript integration
3. `src/news/personalization/generative_recommender.py` → TypeScript integration
4. `src/news/ui/particle_feed.py` → TypeScript React component

## 📋 Integration Requirements

1. **Type Safety**: Full TypeScript interfaces matching Python structures
2. **Fallback Handling**: Graceful degradation if Python services unavailable
3. **Performance**: Non-blocking async patterns for API calls
4. **Error Handling**: Comprehensive error management
5. **Memory Persistence**: State caching for performance

## 📝 Implementation Guide

### Step 1: Create TypeScript Interfaces

```typescript
// src/types/AIModels.ts

export interface ELearnFitResult {
  bookId: string;
  rawScore: number;
  optimizedScore: number;
  confidenceLevel: number;
  optimizationFactors: {
    userPreference: number;
    trending: number;
    contextual: number;
  };
}

export interface ScoreRAGSummary {
  originalText: string;
  summaryText: string;
  summaryScore: number;
  keyInsights: string[];
  sentimentScore: number;
}

export interface GenerativeRecommendation {
  bookId: string;
  title: string;
  author: string;
  score: number;
  explanation: string;
  matchFactors: {
    genreMatch: number;
    styleMatch: number;
    themeMatch: number;
    complexityMatch: number;
  };
}

export interface ParticleFeedVisualization {
  nodes: Array<{
    id: string;
    title: string;
    size: number;
    group: number;
  }>;
  links: Array<{
    source: string;
    target: string;
    value: number;
  }>;
}
```

### Step 2: Create API Service

```typescript
// src/services/AIApiService.ts

import {
  ELearnFitResult,
  ScoreRAGSummary,
  GenerativeRecommendation,
} from "../types/AIModels";
import { Book } from "../types/Book";

class AIApiService {
  private baseUrl: string = "/api/ai";
  private cache = new Map<string, any>();

  // Cache TTL in milliseconds (5 minutes)
  private cacheTTL: number = 5 * 60 * 1000;

  // Helper to handle API responses with caching
  private async fetchWithCache<T>(
    endpoint: string,
    params: Record<string, any> = {},
    cacheKey?: string
  ): Promise<T> {
    // Generate cache key if not provided
    const key = cacheKey || `${endpoint}:${JSON.stringify(params)}`;

    // Check cache first
    const cached = this.cache.get(key);
    if (cached && cached.expiry > Date.now()) {
      return cached.data as T;
    }

    try {
      // Build URL with query params
      const url = new URL(`${this.baseUrl}/${endpoint}`);
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value.toString());
      });

      // Fetch from API
      const response = await fetch(url.toString());

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      // Cache the result
      this.cache.set(key, {
        data,
        expiry: Date.now() + this.cacheTTL,
      });

      return data as T;
    } catch (error) {
      console.error(`Error fetching from ${endpoint}:`, error);
      throw error;
    }
  }

  // ELearnFit Optimizer API
  async getOptimizedScore(book: Book): Promise<ELearnFitResult> {
    try {
      return await this.fetchWithCache<ELearnFitResult>(
        "optimize-score",
        { bookId: book.id },
        `optimize-score:${book.id}`
      );
    } catch (error) {
      // Fallback if API fails
      return {
        bookId: book.id,
        rawScore: book.score || 0.5,
        optimizedScore: book.score || 0.5,
        confidenceLevel: 0.7,
        optimizationFactors: {
          userPreference: 0.5,
          trending: 0.5,
          contextual: 0.5,
        },
      };
    }
  }

  // ScoreRAG Summarization API
  async getSummary(text: string): Promise<ScoreRAGSummary> {
    if (!text) return null;

    try {
      return await this.fetchWithCache<ScoreRAGSummary>(
        "summarize",
        { text },
        `summarize:${text.substring(0, 50)}`
      );
    } catch (error) {
      // Fallback if API fails
      return {
        originalText: text,
        summaryText: text.substring(0, 100) + "...",
        summaryScore: 0.5,
        keyInsights: [],
        sentimentScore: 0,
      };
    }
  }

  // Generative Recommender API
  async getRecommendations(
    userId: string
  ): Promise<GenerativeRecommendation[]> {
    try {
      return await this.fetchWithCache<GenerativeRecommendation[]>(
        "recommendations",
        { userId },
        `recommendations:${userId}`
      );
    } catch (error) {
      // Fallback if API fails
      return [
        {
          bookId: "1",
          title: "The Pragmatic Programmer",
          author: "Hunt & Thomas",
          score: 0.95,
          explanation: "Matches your interest in software engineering",
          matchFactors: {
            genreMatch: 0.9,
            styleMatch: 0.8,
            themeMatch: 0.7,
            complexityMatch: 0.6,
          },
        },
        {
          bookId: "2",
          title: "Clean Code",
          author: "Robert C. Martin",
          score: 0.92,
          explanation: "Based on your reading history",
          matchFactors: {
            genreMatch: 0.9,
            styleMatch: 0.8,
            themeMatch: 0.7,
            complexityMatch: 0.6,
          },
        },
      ];
    }
  }
}

export const aiService = new AIApiService();
```

### Step 3: Create TypeScript Wrapper Classes

```typescript
// src/news/ai/elearnfit_optimizer.ts

import { Book } from "../../types/Book";
import { ELearnFitResult } from "../../types/AIModels";
import { aiService } from "../../services/AIApiService";

export class ELearnFitOptimizer {
  // Static method for easy access
  static async getOptimizedScore(book: Book): Promise<number> {
    try {
      const result = await aiService.getOptimizedScore(book);
      return result.optimizedScore;
    } catch (error) {
      console.error("Error in ELearnFit optimization:", error);
      return book.score || 0.5;
    }
  }

  // Instance method for more detailed results
  async optimizeScore(book: Book): Promise<ELearnFitResult> {
    try {
      return await aiService.getOptimizedScore(book);
    } catch (error) {
      console.error("Error in ELearnFit optimization:", error);
      return {
        bookId: book.id,
        rawScore: book.score || 0.5,
        optimizedScore: book.score || 0.5,
        confidenceLevel: 0.7,
        optimizationFactors: {
          userPreference: 0.5,
          trending: 0.5,
          contextual: 0.5,
        },
      };
    }
  }
}
```

```typescript
// src/news/ai/scorerag_summarization.ts

import { ScoreRAGSummary } from "../../types/AIModels";
import { aiService } from "../../services/AIApiService";

export class ScoreRAGSummarization {
  // Static method for easy access
  static async getSummary(text: string): Promise<string> {
    if (!text) return "";

    try {
      const result = await aiService.getSummary(text);
      return result.summaryText;
    } catch (error) {
      console.error("Error in ScoreRAG summarization:", error);
      return text.substring(0, 100) + "...";
    }
  }

  // Instance method for more detailed results
  async summarize(text: string): Promise<ScoreRAGSummary> {
    if (!text) return null;

    try {
      return await aiService.getSummary(text);
    } catch (error) {
      console.error("Error in ScoreRAG summarization:", error);
      return {
        originalText: text,
        summaryText: text.substring(0, 100) + "...",
        summaryScore: 0.5,
        keyInsights: [],
        sentimentScore: 0,
      };
    }
  }
}
```

### Step 4: Create React Component for ParticleFeed

```tsx
// src/news/ui/particle_feed.tsx

import React, { useRef, useEffect } from "react";
import { useSelector } from "react-redux";
import * as d3 from "d3";
import { Book } from "../../types/Book";
import { RootState } from "../../stores/store";

interface ParticleFeedProps {
  books: Book[];
  width?: number;
  height?: number;
}

export const ParticleFeed: React.FC<ParticleFeedProps> = ({
  books,
  width = 600,
  height = 400,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const theme = useSelector((state: RootState) => state.ui.theme);

  useEffect(() => {
    if (!svgRef.current || !books.length) return;

    // Clear previous visualization
    d3.select(svgRef.current).selectAll("*").remove();

    // Create nodes from books
    const nodes = books.map((book) => ({
      id: book.id,
      title: book.title,
      radius: 10 + (book.score || 0.5) * 20,
      group: Math.floor(Math.random() * 5),
    }));

    // Create links between related books
    const links = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        if (Math.random() > 0.7) {
          links.push({
            source: nodes[i].id,
            target: nodes[j].id,
            value: Math.random(),
          });
        }
      }
    }

    // Set up force simulation
    const simulation = d3
      .forceSimulation()
      .force(
        "link",
        d3
          .forceLink()
          .id((d: any) => d.id)
          .distance(100)
      )
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // Create SVG container
    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("class", "particle-feed");

    // Add links
    const link = svg
      .append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr(
        "stroke",
        theme === "dark" ? "rgba(255,255,255,0.2)" : "rgba(0,0,0,0.2)"
      )
      .attr("stroke-width", (d: any) => Math.sqrt(d.value) * 2);

    // Add nodes
    const node = svg
      .append("g")
      .attr("class", "nodes")
      .selectAll("circle")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("r", (d: any) => d.radius)
      .attr("fill", (d: any) => d3.schemeCategory10[d.group])
      .attr("stroke", theme === "dark" ? "#fff" : "#000")
      .attr("stroke-width", 1.5)
      .call(
        d3
          .drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended)
      );

    // Add tooltips
    node.append("title").text((d: any) => d.title);

    // Update positions on tick
    simulation.nodes(nodes).on("tick", ticked);
    simulation.force<d3.ForceLink<any, any>>("link").links(links);

    function ticked() {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);
    }

    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: any) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [books, width, height, theme]);

  return (
    <div className="particle-feed-container">
      <svg ref={svgRef} className={`particle-feed particle-feed--${theme}`} />
    </div>
  );
};
```

### Step 5: Create FastAPI Endpoints to Bridge Python Models

```python
# src/api/ai_endpoints.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from ..news.ai.elearnfit_optimizer import ELearnFitOptimizer
from ..news.ai.scorerag_summarization import ScoreRAGSummarization
from ..news.personalization.generative_recommender import GenerativeRecommender

router = APIRouter(prefix="/api/ai", tags=["AI"])

# Models matching TypeScript interfaces
class OptimizationFactors(BaseModel):
    userPreference: float = Field(..., ge=0, le=1)
    trending: float = Field(..., ge=0, le=1)
    contextual: float = Field(..., ge=0, le=1)

class ELearnFitResult(BaseModel):
    bookId: str
    rawScore: float = Field(..., ge=0, le=1)
    optimizedScore: float = Field(..., ge=0, le=1)
    confidenceLevel: float = Field(..., ge=0, le=1)
    optimizationFactors: OptimizationFactors

class ScoreRAGSummary(BaseModel):
    originalText: str
    summaryText: str
    summaryScore: float = Field(..., ge=0, le=1)
    keyInsights: List[str]
    sentimentScore: float = Field(..., ge=-1, le=1)

class MatchFactors(BaseModel):
    genreMatch: float = Field(..., ge=0, le=1)
    styleMatch: float = Field(..., ge=0, le=1)
    themeMatch: float = Field(..., ge=0, le=1)
    complexityMatch: float = Field(..., ge=0, le=1)

class GenerativeRecommendation(BaseModel):
    bookId: str
    title: str
    author: str
    score: float = Field(..., ge=0, le=1)
    explanation: str
    matchFactors: MatchFactors

# Initialize AI components
elearnfit = ELearnFitOptimizer()
scorerag = ScoreRAGSummarization()
recommender = GenerativeRecommender()

@router.get("/optimize-score", response_model=ELearnFitResult)
async def get_optimized_score(bookId: str):
    try:
        result = elearnfit.optimize_score(bookId)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")

@router.get("/summarize", response_model=ScoreRAGSummary)
async def get_summary(text: str):
    try:
        result = scorerag.summarize(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization error: {str(e)}")

@router.get("/recommendations", response_model=List[GenerativeRecommendation])
async def get_recommendations(userId: str):
    try:
        recommendations = recommender.get_recommendations(userId)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")
```

## 🧪 Testing the Integration

Test the integration by:

1. Starting the FastAPI backend with `uvicorn src.api.main:app --reload`
2. Running the React frontend with `npm run dev`
3. Checking browser console for any API errors
4. Verifying data flows from Python to React components

## 🚀 Key Benefits

This integration approach provides:

1. **Type Safety**: Full TypeScript interfaces matching Python data structures
2. **Resilience**: Graceful fallbacks if backend services are unavailable
3. **Performance**: Caching and non-blocking async patterns
4. **Maintainability**: Clean separation of concerns
5. **Production-Readiness**: Error handling and monitoring

## 📝 Next Steps After Implementation

1. Add comprehensive error logging
2. Implement API request batching for performance
3. Add unit tests for both TypeScript adapters and Python models
4. Implement offline mode with IndexedDB for persistent caching
5. Add telemetry to track AI component performance

Following these guidelines will ensure a seamless integration between our Python AI components and React frontend, fixing the dashboard UI issues while maintaining type safety and performance.
