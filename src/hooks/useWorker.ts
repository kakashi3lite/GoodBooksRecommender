/**
 * 🧵 Web Worker Hook
 * Chain-of-Thought: Offload CPU-intensive tasks to background threads
 * Memory: Preserve UI responsiveness for complex operations
 * Forward-Thinking: Support for transferable objects and shared memory
 */

import { useRef, useEffect, useCallback, useState } from 'react';

interface UseWorkerOptions {
  transferable?: boolean;
  timeout?: number;
}

type WorkerMessageHandler = (message: any) => void;

/**
 * Custom hook for easy Web Worker usage
 * Chain-of-Thought: Move CPU-heavy processing off the main thread
 * Time Complexity: O(1) messaging, non-blocking execution
 * 
 * @param workerUrl URL to the worker script
 * @param onMessage Callback for handling worker messages
 * @param options Configuration options
 */
export const useWorker = (
  workerUrl: string | URL,
  onMessage?: WorkerMessageHandler,
  options: UseWorkerOptions = {}
) => {
  // Reference to worker instance
  const workerRef = useRef<Worker | null>(null);
  
  // Track loading and error states
  const [isReady, setIsReady] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  
  /**
   * Initialize worker on mount
   * Chain-of-Thought: Create worker once and clean up on unmount
   */
  useEffect(() => {
    try {
      // Create worker
      workerRef.current = new Worker(workerUrl);
      setIsReady(true);
      
      // Set up message handler
      if (onMessage) {
        workerRef.current.onmessage = (event) => {
          onMessage(event.data);
        };
      }
      
      // Handle errors
      workerRef.current.onerror = (err) => {
        console.error('Worker error:', err);
        setError(new Error(`Worker error: ${err.message}`));
      };
      
      // Cleanup on unmount
      return () => {
        workerRef.current?.terminate();
        workerRef.current = null;
      };
    } catch (err) {
      console.error('Failed to initialize worker:', err);
      setError(err instanceof Error ? err : new Error('Failed to initialize worker'));
      return undefined;
    }
  }, [workerUrl, onMessage]);
  
  /**
   * Send message to worker
   * Chain-of-Thought: Support transferable objects for zero-copy transfers
   */
  const sendMessage = useCallback(
    (message: any, transferList?: Transferable[]) => {
      if (!workerRef.current) {
        console.error('Worker not initialized');
        return;
      }
      
      try {
        // Use transferable objects if available and enabled
        if (options.transferable && transferList) {
          workerRef.current.postMessage(message, transferList);
        } else {
          workerRef.current.postMessage(message);
        }
      } catch (err) {
        console.error('Error sending message to worker:', err);
        setError(err instanceof Error ? err : new Error('Error sending message to worker'));
      }
    },
    [options.transferable]
  );
  
  /**
   * Execute a task with timeout
   * Chain-of-Thought: Support timeouts for long-running tasks
   */
  const executeTask = useCallback(
    (taskData: any, transferList?: Transferable[]): Promise<any> => {
      return new Promise((resolve, reject) => {
        if (!workerRef.current) {
          reject(new Error('Worker not initialized'));
          return;
        }
        
        // Generate a unique ID for this task
        const taskId = `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        // Set up a one-time message handler for this task
        const messageHandler = (event: MessageEvent) => {
          const { id, result, error } = event.data;
          
          if (id === taskId) {
            // Remove event listener
            workerRef.current?.removeEventListener('message', messageHandler);
            
            // Clear timeout if set
            if (timeoutId) {
              clearTimeout(timeoutId);
            }
            
            if (error) {
              reject(new Error(error));
            } else {
              resolve(result);
            }
          }
        };
        
        workerRef.current.addEventListener('message', messageHandler);
        
        // Set timeout if specified
        let timeoutId: NodeJS.Timeout | undefined;
        if (options.timeout) {
          timeoutId = setTimeout(() => {
            workerRef.current?.removeEventListener('message', messageHandler);
            reject(new Error(`Task timed out after ${options.timeout}ms`));
          }, options.timeout);
        }
        
        // Send the task to the worker
        try {
          if (options.transferable && transferList) {
            workerRef.current.postMessage({ id: taskId, data: taskData }, transferList);
          } else {
            workerRef.current.postMessage({ id: taskId, data: taskData });
          }
        } catch (err) {
          // Clean up
          workerRef.current.removeEventListener('message', messageHandler);
          if (timeoutId) {
            clearTimeout(timeoutId);
          }
          
          reject(err instanceof Error ? err : new Error('Error sending message to worker'));
        }
      });
    },
    [options.timeout, options.transferable]
  );
  
  /**
   * Terminate the worker
   * Chain-of-Thought: Provide clean shutdown capability
   */
  const terminateWorker = useCallback(() => {
    if (workerRef.current) {
      workerRef.current.terminate();
      workerRef.current = null;
      setIsReady(false);
    }
  }, []);
  
  return {
    worker: workerRef.current,
    isReady,
    error,
    sendMessage,
    executeTask,
    terminateWorker
  };
};

export default useWorker;
