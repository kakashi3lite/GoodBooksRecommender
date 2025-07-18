/**
 * 🤖 ScoreRAG Summarization TypeScript Adapter
 * TypeScript wrapper for the Python ScoreRAG summarization system
 */

import { ScoreRAGSummary } from '../../types/AIModels'
import { aiService } from '../../services/AIApiService'

export class ScoreRAGSummarization {
  private static instance: ScoreRAGSummarization
  private modelVersion = '2.0.0'
  private isInitialized = false

  private constructor() {
    this.initialize()
  }

  public static getInstance(): ScoreRAGSummarization {
    if (!ScoreRAGSummarization.instance) {
      ScoreRAGSummarization.instance = new ScoreRAGSummarization()
    }
    return ScoreRAGSummarization.instance
  }

  private async initialize(): Promise<void> {
    try {
      this.isInitialized = true
      console.log(`🤖 ScoreRAG Summarization TypeScript v${this.modelVersion} initialized`)
    } catch (error) {
      console.error('Failed to initialize ScoreRAG Summarization:', error)
      this.isInitialized = false
    }
  }

  /**
   * Get summary for a text using AI service
   * @param text - The text to summarize
   * @returns Promise resolving to summary text
   */
  public static async getSummary(text: string): Promise<string> {
    if (!text || text.length < 10) return ''
    
    try {
      const result = await aiService.getSummary(text)
      return result?.summaryText || ''
    } catch (error) {
      console.warn('Error getting summary:', error)
      // Return fallback summary
      const sentences = text.split('.').filter(s => s.trim().length > 0)
      return sentences.slice(0, 2).join('.') + '.'
    }
  }

  /**
   * Get detailed summary result
   * @param text - The text to summarize
   * @returns Promise resolving to detailed summary result
   */
  public async getSummaryResult(text: string): Promise<ScoreRAGSummary | null> {
    if (!text || text.length < 10) return null
    
    try {
      return await aiService.getSummary(text)
    } catch (error) {
      console.warn('Error getting summary result:', error)
      return null
    }
  }

  /**
   * Summarize with custom options
   * @param text - The text to summarize
   * @param options - Summarization options
   * @returns Promise resolving to summary result
   */
  public async summarizeWithOptions(
    text: string,
    options: {
      maxLength?: number
      includeKeyInsights?: boolean
      includeSentiment?: boolean
      complexity?: 'simple' | 'detailed'
    } = {}
  ): Promise<ScoreRAGSummary | null> {
    if (!text || text.length < 10) return null

    const {
      maxLength = 200,
      includeKeyInsights = true,
      includeSentiment = true
    } = options

    try {
      // For now, use the basic summary service
      // In the future, this could accept additional parameters
      const result = await aiService.getSummary(text.substring(0, maxLength * 5))
      
      if (!result) return null

      // Apply options to the result
      if (!includeKeyInsights) {
        result.keyInsights = []
      }
      
      if (!includeSentiment) {
        result.sentimentScore = 0
      }

      return result
    } catch (error) {
      console.warn('Error in summarizeWithOptions:', error)
      return null
    }
  }

  /**
   * Batch summarize multiple texts
   * @param texts - Array of texts to summarize
   * @returns Promise resolving to array of summaries
   */
  public async batchSummarize(texts: string[]): Promise<(ScoreRAGSummary | null)[]> {
    const promises = texts.map(text => this.getSummaryResult(text))
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
        'text_summarization',
        'key_insight_extraction',
        'sentiment_analysis',
        'theme_identification',
        'complexity_analysis',
        'batch_processing'
      ]
    }
  }

  /**
   * Extract key insights from text
   * @param text - The text to analyze
   * @returns Promise resolving to key insights
   */
  public async extractKeyInsights(text: string): Promise<string[]> {
    try {
      const result = await this.getSummaryResult(text)
      return result?.keyInsights || []
    } catch (error) {
      console.warn('Error extracting key insights:', error)
      return []
    }
  }

  /**
   * Analyze sentiment of text
   * @param text - The text to analyze
   * @returns Promise resolving to sentiment score (-1 to 1)
   */
  public async analyzeSentiment(text: string): Promise<number> {
    try {
      const result = await this.getSummaryResult(text)
      return result?.sentimentScore || 0
    } catch (error) {
      console.warn('Error analyzing sentiment:', error)
      return 0
    }
  }
}
