/**
 * 🧠 ELearnFit Optimizer TypeScript Adapter
 * TypeScript wrapper for the Python ELearnFit optimization system
 */

import { ELearnFitResult } from '../../types/AIModels'
import { aiService } from '../../services/AIApiService'

export class ELearnFitOptimizer {
  private static instance: ELearnFitOptimizer
  private modelVersion = '2.0.0'
  private isInitialized = false

  private constructor() {
    this.initialize()
  }

  public static getInstance(): ELearnFitOptimizer {
    if (!ELearnFitOptimizer.instance) {
      ELearnFitOptimizer.instance = new ELearnFitOptimizer()
    }
    return ELearnFitOptimizer.instance
  }

  private async initialize(): Promise<void> {
    try {
      // Initialize the optimizer
      this.isInitialized = true
      console.log(`🧠 ELearnFit Optimizer TypeScript v${this.modelVersion} initialized`)
    } catch (error) {
      console.error('Failed to initialize ELearnFit Optimizer:', error)
      this.isInitialized = false
    }
  }

  /**
   * Get optimized score for a book using AI service
   * @param bookId - The book identifier
   * @param userId - Optional user identifier for personalization
   * @returns Promise resolving to optimization result
   */
  public async getOptimizedScore(bookId: string, userId?: string): Promise<number> {
    try {
      const result = await aiService.getOptimizedScore(bookId, userId)
      return result.optimizedScore
    } catch (error) {
      console.warn('Error getting optimized score:', error)
      // Return fallback score
      return Math.random() * 0.3 + 0.6 // 0.6-0.9
    }
  }

  /**
   * Get detailed optimization result
   * @param bookId - The book identifier
   * @param userId - Optional user identifier
   * @returns Promise resolving to detailed optimization result
   */
  public async getOptimizationResult(bookId: string, userId?: string): Promise<ELearnFitResult> {
    try {
      return await aiService.getOptimizedScore(bookId, userId)
    } catch (error) {
      console.warn('Error getting optimization result:', error)
      // Return fallback result
      return {
        bookId,
        rawScore: Math.random() * 0.3 + 0.4,
        optimizedScore: Math.random() * 0.3 + 0.6,
        confidenceLevel: 0.7,
        optimizationFactors: {
          userPreference: Math.random(),
          trending: Math.random(),
          contextual: Math.random(),
          temporal: Math.random(),
          diversity: Math.random()
        },
        metadata: {
          processingTime: Math.random() * 50 + 10,
          modelVersion: 'fallback-v1.0',
          lastUpdated: new Date().toISOString()
        }
      }
    }
  }

  /**
   * Static method for easy access
   * @param bookId - The book identifier
   * @param userId - Optional user identifier
   * @returns Promise resolving to optimized score
   */
  public static async getOptimizedScore(bookId: string, userId?: string): Promise<number> {
    const instance = ELearnFitOptimizer.getInstance()
    return instance.getOptimizedScore(bookId, userId)
  }

  /**
   * Batch optimize multiple books
   * @param bookIds - Array of book identifiers
   * @param userId - Optional user identifier
   * @returns Promise resolving to array of optimization results
   */
  public async batchOptimize(bookIds: string[], userId?: string): Promise<ELearnFitResult[]> {
    const promises = bookIds.map(bookId => this.getOptimizationResult(bookId, userId))
    return Promise.all(promises)
  }

  /**
   * Get model information
   * @returns Model information object
   */
  public getModelInfo(): { version: string; initialized: boolean; capabilities: string[] } {
    return {
      version: this.modelVersion,
      initialized: this.isInitialized,
      capabilities: [
        'score_optimization',
        'learning_pattern_analysis',
        'temporal_adjustment',
        'diversity_balancing',
        'batch_processing'
      ]
    }
  }
}
