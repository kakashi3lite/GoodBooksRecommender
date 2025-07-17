/**
 * 🔄 Virtualized List Hook
 * Chain-of-Thought: Optimize rendering large lists with O(windowSize) complexity
 * Memory: Maintain references to visible elements only
 * Forward-Thinking: Support for different virtualization strategies
 */

import { useState, useEffect, useMemo } from 'react';

interface VirtualizationOptions {
  itemCount: number;
  itemSize: number;
  overscan?: number;
  direction?: 'vertical' | 'horizontal';
}

interface VirtualizedState {
  startIndex: number;
  endIndex: number;
  visibleItems: number[];
  scrollToIndex: (index: number) => void;
  containerProps: {
    style: React.CSSProperties;
    onScroll: (event: React.UIEvent) => void;
  };
  itemProps: (index: number) => {
    style: React.CSSProperties;
    key: number;
  };
}

/**
 * Custom hook for creating virtualized lists
 * Chain-of-Thought: Only render items visible in the viewport plus overscan
 * Time Complexity: Reduces O(n) rendering to O(windowSize)
 * 
 * @param options Configuration options for virtualization
 * @param containerRef Reference to the container element
 */
export const useVirtualizedList = (
  options: VirtualizationOptions,
  containerRef: React.RefObject<HTMLElement>
): VirtualizedState => {
  const { itemCount, itemSize, overscan = 3, direction = 'vertical' } = options;
  
  // Track scroll position
  const [scrollOffset, setScrollOffset] = useState<number>(0);
  
  // Track container dimensions
  const [containerSize, setContainerSize] = useState<number>(0);
  
  // Update container size when it changes
  useEffect(() => {
    if (!containerRef.current) return;
    
    const updateContainerSize = () => {
      if (!containerRef.current) return;
      
      const newSize = direction === 'vertical'
        ? containerRef.current.clientHeight
        : containerRef.current.clientWidth;
        
      setContainerSize(newSize);
    };
    
    // Set initial size
    updateContainerSize();
    
    // Setup resize observer
    const resizeObserver = new ResizeObserver(updateContainerSize);
    resizeObserver.observe(containerRef.current);
    
    return () => {
      if (containerRef.current) {
        resizeObserver.unobserve(containerRef.current);
      }
      resizeObserver.disconnect();
    };
  }, [containerRef, direction]);
  
  /**
   * Calculate visible range with overscan
   * Chain-of-Thought: Only compute indices for items in view plus buffer
   * Time Complexity: O(1) calculation
   */
  const { startIndex, endIndex, visibleItems } = useMemo(() => {
    if (containerSize === 0) {
      return { startIndex: 0, endIndex: 10, visibleItems: [] };
    }
    
    // Calculate the range of visible items
    const itemsPerView = Math.ceil(containerSize / itemSize);
    const start = Math.floor(scrollOffset / itemSize);
    const startWithOverscan = Math.max(0, start - overscan);
    const endWithOverscan = Math.min(itemCount - 1, start + itemsPerView + overscan);
    
    // Generate array of visible indices
    const visibleIndices = Array.from(
      { length: endWithOverscan - startWithOverscan + 1 },
      (_, i) => i + startWithOverscan
    );
    
    return {
      startIndex: startWithOverscan,
      endIndex: endWithOverscan,
      visibleItems: visibleIndices
    };
  }, [scrollOffset, containerSize, itemSize, itemCount, overscan]);
  
  /**
   * Handle scroll events
   * Chain-of-Thought: Update visible items when scroll position changes
   * Time Complexity: O(1) update
   */
  const handleScroll = (event: React.UIEvent) => {
    const target = event.target as HTMLElement;
    const newOffset = direction === 'vertical'
      ? target.scrollTop
      : target.scrollLeft;
      
    setScrollOffset(newOffset);
  };
  
  /**
   * Scroll to a specific item
   * Chain-of-Thought: Programmatically adjust scroll position
   * Time Complexity: O(1) operation
   */
  const scrollToIndex = (index: number) => {
    if (!containerRef.current) return;
    
    // Calculate scroll position
    const scrollPosition = index * itemSize;
    
    // Apply scroll
    if (direction === 'vertical') {
      containerRef.current.scrollTop = scrollPosition;
    } else {
      containerRef.current.scrollLeft = scrollPosition;
    }
  };
  
  /**
   * Calculate total size and item positioning
   * Chain-of-Thought: Create styles for container and items
   * Time Complexity: O(1) per item
   */
  const totalSize = itemCount * itemSize;
  
  // Container props for attaching scroll handler
  const containerProps = {
    style: {
      ...(direction === 'vertical'
        ? { height: '100%', overflowY: 'auto' }
        : { width: '100%', overflowX: 'auto' }),
    },
    onScroll: handleScroll
  };
  
  /**
   * Generate props for individual list items
   * Time Complexity: O(1) per visible item
   */
  const itemProps = (index: number) => ({
    style: {
      position: 'absolute',
      ...(direction === 'vertical'
        ? { top: `${index * itemSize}px`, left: 0, width: '100%', height: `${itemSize}px` }
        : { left: `${index * itemSize}px`, top: 0, width: `${itemSize}px`, height: '100%' }),
    },
    key: index
  });
  
  return {
    startIndex,
    endIndex,
    visibleItems,
    scrollToIndex,
    containerProps,
    itemProps
  };
};

export default useVirtualizedList;
