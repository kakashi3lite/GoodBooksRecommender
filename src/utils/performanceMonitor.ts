/**
 * 🚀 Performance Monitoring Utilities
 * Chain-of-Thought: Track and optimize performance metrics for dashboard components
 * Memory: Store performance snapshots for analysis
 * Forward-Thinking: Implement adaptive performance optimizations
 */

import React from 'react';
import { updateRenderTime, updateApiLatency } from '../stores/dashboard/dashboardSlice';
import { store } from '../stores/store';

/**
 * Class for tracking and optimizing component performance
 * Chain-of-Thought: Measure render times and API latency with minimal overhead
 * Time Complexity: O(1) overhead per tracked component or API call
 */
export class PerformanceMonitor {
  private static renderTimers: Map<string, number> = new Map();
  private static apiTimers: Map<string, number> = new Map();
  private static performanceSnapshots: any[] = [];
  
  // Max snapshots to keep (sliding window)
  private static readonly MAX_SNAPSHOTS = 100;
  
  /**
   * Start timing component render
   * Time Complexity: O(1)
   */
  static startRenderTimer(componentId: string): void {
    this.renderTimers.set(componentId, performance.now());
  }
  
  /**
   * End timing component render and dispatch to store
   * Time Complexity: O(1)
   */
  static endRenderTimer(componentId: string): number | null {
    const startTime = this.renderTimers.get(componentId);
    
    if (!startTime) {
      console.warn(`No start time found for component ${componentId}`);
      return null;
    }
    
    const renderTime = performance.now() - startTime;
    this.renderTimers.delete(componentId);
    
    // Add to performance metrics
    store.dispatch(updateRenderTime(renderTime));
    
    // Take snapshot if render time is suspiciously high
    if (renderTime > 100) { // 100ms threshold
      this.takePerformanceSnapshot({
        type: 'render',
        componentId,
        renderTime,
        timestamp: Date.now()
      });
    }
    
    return renderTime;
  }
  
  /**
   * Start timing API call
   * Time Complexity: O(1)
   */
  static startApiTimer(endpoint: string): void {
    this.apiTimers.set(endpoint, performance.now());
  }
  
  /**
   * End timing API call and dispatch to store
   * Time Complexity: O(1)
   */
  static endApiTimer(endpoint: string): number | null {
    const startTime = this.apiTimers.get(endpoint);
    
    if (!startTime) {
      console.warn(`No start time found for API call to ${endpoint}`);
      return null;
    }
    
    const latency = performance.now() - startTime;
    this.apiTimers.delete(endpoint);
    
    // Add to performance metrics
    store.dispatch(updateApiLatency({ endpoint, latency }));
    
    // Take snapshot if latency is suspiciously high
    if (latency > 500) { // 500ms threshold
      this.takePerformanceSnapshot({
        type: 'api',
        endpoint,
        latency,
        timestamp: Date.now()
      });
    }
    
    return latency;
  }
  
  /**
   * Create a HOC for performance monitoring
   * Chain-of-Thought: Wrap components to automatically track render times
   * Time Complexity: O(1) overhead per render
   */
  static withPerformanceTracking<P extends object>(
    WrappedComponent: React.ComponentType<P>,
    componentId: string
  ): React.FC<P> {
    return function PerformanceTrackedComponent(props: P) {
      React.useEffect(() => {
        PerformanceMonitor.startRenderTimer(componentId);
        
        return () => {
          PerformanceMonitor.endRenderTimer(componentId);
        };
      }, []);
      
      return React.createElement(WrappedComponent, props);
    };
  }
  
  /**
   * Create a performance measurement hook
   * Chain-of-Thought: Custom hook for React components to measure render times
   * Time Complexity: O(1) overhead per render
   */
  static usePerformanceTracking(componentId: string): void {
    React.useEffect(() => {
      PerformanceMonitor.startRenderTimer(componentId);
      
      return () => {
        PerformanceMonitor.endRenderTimer(componentId);
      };
    }, [componentId]);
  }
  
  /**
   * Track API call with automatic timing
   * Time Complexity: O(1) overhead per API call
   */
  static async trackApiCall<T>(
    endpoint: string, 
    apiCall: () => Promise<T>
  ): Promise<T> {
    this.startApiTimer(endpoint);
    
    try {
      const result = await apiCall();
      this.endApiTimer(endpoint);
      return result;
    } catch (error) {
      this.endApiTimer(endpoint);
      throw error;
    }
  }
  
  /**
   * Take a snapshot of current performance state
   * Chain-of-Thought: Store performance data for analysis and debugging
   * Time Complexity: O(1) with sliding window for memory efficiency
   */
  static takePerformanceSnapshot(data: any): void {
    const memoryInfo = (performance as any).memory;
    const snapshot = {
      ...data,
      jsHeapSize: memoryInfo ? memoryInfo.usedJSHeapSize : null,
      timestamp: Date.now()
    };
    
    // Add snapshot to sliding window
    this.performanceSnapshots.push(snapshot);
    
    // Keep array size bounded
    if (this.performanceSnapshots.length > this.MAX_SNAPSHOTS) {
      this.performanceSnapshots.shift();
    }
    
    // Log to console in development mode
    if (process.env.NODE_ENV === 'development') {
      console.debug('Performance snapshot:', snapshot);
    }
  }
  
  /**
   * Get all performance snapshots
   * Chain-of-Thought: Retrieve performance data for analysis
   * Time Complexity: O(1)
   */
  static getPerformanceSnapshots(): any[] {
    return [...this.performanceSnapshots];
  }
  
  /**
   * Get performance analytics and insights
   * Chain-of-Thought: Analyze performance trends and provide optimization suggestions
   * Time Complexity: O(n) where n is number of snapshots
   */
  static getPerformanceAnalytics(): any {
    if (this.performanceSnapshots.length === 0) {
      return {
        averageRenderTime: 0,
        averageApiLatency: 0,
        slowestComponent: null,
        slowestApi: null,
        optimizationSuggestions: []
      };
    }
    
    // Group snapshots by type
    const renderSnapshots = this.performanceSnapshots.filter(s => s.type === 'render');
    const apiSnapshots = this.performanceSnapshots.filter(s => s.type === 'api');
    
    // Calculate averages
    const avgRenderTime = renderSnapshots.length > 0
      ? renderSnapshots.reduce((sum, s) => sum + s.renderTime, 0) / renderSnapshots.length
      : 0;
      
    const avgApiLatency = apiSnapshots.length > 0
      ? apiSnapshots.reduce((sum, s) => sum + s.latency, 0) / apiSnapshots.length
      : 0;
    
    // Find slowest components and APIs
    const componentStats: Record<string, { count: number, totalTime: number }> = {};
    const endpointStats: Record<string, { count: number, totalTime: number }> = {};
    
    renderSnapshots.forEach(s => {
      if (!componentStats[s.componentId]) {
        componentStats[s.componentId] = { count: 0, totalTime: 0 };
      }
      componentStats[s.componentId].count++;
      componentStats[s.componentId].totalTime += s.renderTime;
    });
    
    apiSnapshots.forEach(s => {
      if (!endpointStats[s.endpoint]) {
        endpointStats[s.endpoint] = { count: 0, totalTime: 0 };
      }
      endpointStats[s.endpoint].count++;
      endpointStats[s.endpoint].totalTime += s.latency;
    });
    
    // Get averages by component/endpoint
    const componentAverages = Object.entries(componentStats).map(([id, stats]) => ({
      componentId: id,
      averageTime: stats.totalTime / stats.count,
      count: stats.count
    }));
    
    const endpointAverages = Object.entries(endpointStats).map(([endpoint, stats]) => ({
      endpoint,
      averageLatency: stats.totalTime / stats.count,
      count: stats.count
    }));
    
    // Sort to find slowest
    componentAverages.sort((a, b) => b.averageTime - a.averageTime);
    endpointAverages.sort((a, b) => b.averageLatency - a.averageLatency);
    
    // Generate optimization suggestions
    const suggestions: string[] = [];
    
    if (componentAverages.length > 0 && componentAverages[0].averageTime > 50) {
      suggestions.push(
        `Consider optimizing the ${componentAverages[0].componentId} component which takes ${componentAverages[0].averageTime.toFixed(2)}ms to render on average.`
      );
    }
    
    if (endpointAverages.length > 0 && endpointAverages[0].averageLatency > 300) {
      suggestions.push(
        `API calls to ${endpointAverages[0].endpoint} are slow (${endpointAverages[0].averageLatency.toFixed(2)}ms). Consider caching or optimizing backend responses.`
      );
    }
    
    if (renderSnapshots.length > 50) {
      suggestions.push(
        'High frequency of component re-renders detected. Consider using React.memo or optimizing state updates.'
      );
    }
    
    return {
      averageRenderTime: avgRenderTime,
      averageApiLatency: avgApiLatency,
      slowestComponent: componentAverages[0] || null,
      slowestApi: endpointAverages[0] || null,
      optimizationSuggestions: suggestions
    };
  }
}

/**
 * React hook for measuring component performance
 * Chain-of-Thought: Easily track render times in functional components
 * Time Complexity: O(1) overhead per render
 */
export const usePerformanceTracking = (componentId: string): void => {
  React.useEffect(() => {
    PerformanceMonitor.startRenderTimer(componentId);
    
    return () => {
      PerformanceMonitor.endRenderTimer(componentId);
    };
  }, [componentId]);
};

/**
 * Higher-order component for performance tracking
 * Chain-of-Thought: Wrap components to track render times
 * Time Complexity: O(1) overhead per render
 */
export const withPerformanceTracking = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  componentId: string
): React.FC<P> => {
  return function TrackedComponent(props: P) {
    usePerformanceTracking(componentId);
    return React.createElement(WrappedComponent, props);
  };
};

/**
 * Create API client wrapper with performance tracking
 * Chain-of-Thought: Monitor API latency in a middleware-like pattern
 * Time Complexity: O(1) overhead per API call
 */
export const createPerformanceApiClient = (baseClient: any) => {
  return new Proxy(baseClient, {
    get: (target, prop) => {
      const value = target[prop];
      
      // Only proxy function properties (API methods)
      if (typeof value !== 'function') {
        return value;
      }
      
      return (...args: any[]) => {
        const endpoint = typeof prop === 'string' ? prop : String(prop);
        
        return PerformanceMonitor.trackApiCall(
          endpoint,
          () => value.apply(target, args)
        );
      };
    }
  });
};

export default PerformanceMonitor;

/**
 * Frame Rate Monitor for detecting UI jank
 * Chain-of-Thought: Use requestAnimationFrame to detect frame drops
 * Time Complexity: O(1) per frame with minimal overhead
 */
export class FrameRateMonitor {
  private static isMonitoring = false;
  private static frameCount = 0;
  private static lastFrameTime = 0;
  private static frameTimes: number[] = [];
  private static dropDetectionThreshold = 33.33; // 30fps threshold (33.33ms)
  private static frameDrops: { timestamp: number, duration: number }[] = [];
  private static callback: ((fps: number, drops: number) => void) | null = null;
  
  /**
   * Start monitoring frame rate
   * Time Complexity: O(1)
   */
  static startMonitoring(
    callback?: (fps: number, drops: number) => void,
    options = { dropThreshold: 33.33 }
  ): void {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    this.frameCount = 0;
    this.lastFrameTime = performance.now();
    this.frameTimes = [];
    this.frameDrops = [];
    this.dropDetectionThreshold = options.dropThreshold;
    this.callback = callback || null;
    
    // Start frame monitoring loop
    requestAnimationFrame(this.frameLoop.bind(this));
    
    // Report every second
    setInterval(() => this.reportFrameRate(), 1000);
  }
  
  /**
   * Stop monitoring frame rate
   * Time Complexity: O(1)
   */
  static stopMonitoring(): void {
    this.isMonitoring = false;
    this.callback = null;
  }
  
  /**
   * Frame monitoring loop
   * Time Complexity: O(1) per frame
   */
  private static frameLoop(timestamp: number): void {
    if (!this.isMonitoring) return;
    
    // Calculate frame time
    const frameDuration = timestamp - this.lastFrameTime;
    this.lastFrameTime = timestamp;
    
    // Track frame time
    this.frameTimes.push(frameDuration);
    if (this.frameTimes.length > 60) {
      this.frameTimes.shift(); // Keep last 60 frames
    }
    
    // Detect frame drop
    if (frameDuration > this.dropDetectionThreshold) {
      this.frameDrops.push({
        timestamp,
        duration: frameDuration
      });
      
      // Log severe frame drops
      if (frameDuration > 100) {
        PerformanceMonitor.takePerformanceSnapshot({
          type: 'frame-drop',
          duration: frameDuration,
          timestamp
        });
      }
    }
    
    this.frameCount++;
    
    // Continue monitoring
    requestAnimationFrame(this.frameLoop.bind(this));
  }
  
  /**
   * Calculate and report current frame rate
   * Time Complexity: O(1)
   */
  private static reportFrameRate(): void {
    if (!this.isMonitoring) return;
    
    const fps = this.frameCount;
    this.frameCount = 0;
    
    const recentDrops = this.frameDrops
      .filter(drop => drop.timestamp > performance.now() - 1000)
      .length;
    
    if (this.callback) {
      this.callback(fps, recentDrops);
    }
    
    // Log severe frame rate issues
    if (fps < 30 && recentDrops > 5) {
      PerformanceMonitor.takePerformanceSnapshot({
        type: 'low-fps',
        fps,
        drops: recentDrops,
        timestamp: Date.now()
      });
    }
  }
  
  /**
   * Get average frame time over recent frames
   * Time Complexity: O(n) where n is number of tracked frames (max 60)
   */
  static getAverageFrameTime(): number {
    if (this.frameTimes.length === 0) return 0;
    
    const sum = this.frameTimes.reduce((acc, time) => acc + time, 0);
    return sum / this.frameTimes.length;
  }
  
  /**
   * Get performance report for frame rates
   * Time Complexity: O(n) where n is number of frame drops
   */
  static getFrameRateReport(): {
    averageFps: number;
    drops: number;
    worstDrop: number;
    stableFrameRate: boolean;
  } {
    const avgFrameTime = this.getAverageFrameTime();
    const avgFps = avgFrameTime ? Math.round(1000 / avgFrameTime) : 60;
    
    // Get drops in the last 5 seconds
    const recentTime = performance.now() - 5000;
    const recentDrops = this.frameDrops.filter(drop => drop.timestamp > recentTime);
    
    // Get worst drop duration
    const worstDrop = this.frameDrops.length > 0
      ? Math.max(...this.frameDrops.map(drop => drop.duration))
      : 0;
    
    return {
      averageFps: avgFps,
      drops: recentDrops.length,
      worstDrop,
      stableFrameRate: avgFps >= 55 && recentDrops.length < 3
    };
  }
}

/**
 * Memory Usage Analyzer for detecting memory issues
 * Chain-of-Thought: Monitor memory trends and detect leaks
 * Time Complexity: O(1) per sample with sliding window analysis
 */
export class MemoryAnalyzer {
  private static samples: { timestamp: number, usage: number }[] = [];
  private static readonly MAX_SAMPLES = 20;
  private static intervalId: number | null = null;
  
  /**
   * Start memory usage monitoring
   * Time Complexity: O(1)
   */
  static startMonitoring(intervalMs = 10000): void {
    if (this.intervalId !== null) return;
    
    this.samples = [];
    
    this.intervalId = window.setInterval(() => {
      this.takeSample();
      this.analyzeMemoryTrend();
    }, intervalMs);
  }
  
  /**
   * Stop memory usage monitoring
   * Time Complexity: O(1)
   */
  static stopMonitoring(): void {
    if (this.intervalId === null) return;
    
    window.clearInterval(this.intervalId);
    this.intervalId = null;
  }
  
  /**
   * Take a memory usage sample
   * Time Complexity: O(1)
   */
  private static takeSample(): void {
    const memory = (performance as any).memory;
    if (!memory) return;
    
    const sample = {
      timestamp: Date.now(),
      usage: memory.usedJSHeapSize / (1024 * 1024) // MB
    };
    
    this.samples.push(sample);
    
    // Keep sample size bounded
    if (this.samples.length > this.MAX_SAMPLES) {
      this.samples.shift();
    }
  }
  
  /**
   * Analyze memory usage trend for potential issues
   * Chain-of-Thought: Linear regression to detect consistent growth
   * Time Complexity: O(n) where n is number of samples
   */
  private static analyzeMemoryTrend(): void {
    if (this.samples.length < 5) return; // Need enough samples
    
    // Calculate memory growth rate using linear regression
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    const n = this.samples.length;
    
    // Normalize timestamps to start from 0
    const startTime = this.samples[0].timestamp;
    
    this.samples.forEach(sample => {
      const x = (sample.timestamp - startTime) / 60000; // minutes
      const y = sample.usage;
      
      sumX += x;
      sumY += y;
      sumXY += x * y;
      sumX2 += x * x;
    });
    
    // Calculate slope (MB per minute)
    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    
    // Get current and first memory usage
    const currentUsage = this.samples[this.samples.length - 1].usage;
    const firstUsage = this.samples[0].usage;
    const usageGrowth = currentUsage - firstUsage;
    
    // Detect potential memory leak if consistent growth
    if (slope > 2 && usageGrowth > 20) { // Growing more than 2MB per minute and total growth > 20MB
      PerformanceMonitor.takePerformanceSnapshot({
        type: 'memory-growth',
        slope,
        currentUsage,
        startUsage: firstUsage,
        growthRate: `${slope.toFixed(2)} MB/min`,
        timestamp: Date.now()
      });
    }
  }
  
  /**
   * Get memory usage report
   * Time Complexity: O(n) where n is number of samples
   */
  static getMemoryReport(): {
    currentUsage: number;
    peakUsage: number;
    trend: 'stable' | 'growing' | 'unknown';
    growthRate: number;
  } {
    if (this.samples.length < 2) {
      return {
        currentUsage: this.samples.length > 0 ? this.samples[0].usage : 0,
        peakUsage: this.samples.length > 0 ? this.samples[0].usage : 0,
        trend: 'unknown',
        growthRate: 0
      };
    }
    
    const currentUsage = this.samples[this.samples.length - 1].usage;
    const peakUsage = Math.max(...this.samples.map(s => s.usage));
    
    // Calculate growth rate (MB/min)
    const firstSample = this.samples[0];
    const lastSample = this.samples[this.samples.length - 1];
    const timeSpanMinutes = (lastSample.timestamp - firstSample.timestamp) / 60000;
    const growthRate = timeSpanMinutes > 0 
      ? (lastSample.usage - firstSample.usage) / timeSpanMinutes
      : 0;
      
    // Determine trend
    let trend: 'stable' | 'growing' | 'unknown' = 'unknown';
    if (this.samples.length >= 5) {
      trend = growthRate > 1 ? 'growing' : 'stable';
    }
    
    return {
      currentUsage,
      peakUsage,
      trend,
      growthRate
    };
  }
}
