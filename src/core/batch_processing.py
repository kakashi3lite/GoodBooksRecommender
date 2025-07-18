"""
Batch Processing System for GoodBooks Recommender

This module provides efficient batch processing capabilities including:
- Bulk recommendation generation
- Batch user operations
- Asynchronous task processing
- Progress tracking
- Error handling and retry logic
"""

import asyncio
import uuid
import time
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Union, AsyncGenerator
from collections import defaultdict, deque

from src.core.logging import StructuredLogger

logger = StructuredLogger(__name__)


class BatchStatus(Enum):
    """Batch processing status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class TaskStatus(Enum):
    """Individual task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class BatchTask:
    """Individual task within a batch."""
    task_id: str
    input_data: Any
    output_data: Optional[Any] = None
    status: TaskStatus = TaskStatus.PENDING
    error_message: Optional[str] = None
    retry_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['status'] = self.status.value
        if self.start_time:
            result['start_time'] = self.start_time.isoformat()
        if self.end_time:
            result['end_time'] = self.end_time.isoformat()
        return result


@dataclass
class BatchJob:
    """Batch job containing multiple tasks."""
    batch_id: str
    job_type: str
    tasks: List[BatchTask]
    status: BatchStatus = BatchStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
        self.total_tasks = len(self.tasks)
    
    def update_progress(self):
        """Update batch progress based on task completion."""
        self.completed_tasks = len([t for t in self.tasks if t.status == TaskStatus.COMPLETED])
        self.failed_tasks = len([t for t in self.tasks if t.status == TaskStatus.FAILED])
        
        if self.total_tasks > 0:
            self.progress = (self.completed_tasks + self.failed_tasks) / self.total_tasks
        
        # Update batch status
        if self.completed_tasks == self.total_tasks:
            self.status = BatchStatus.COMPLETED
            if not self.completed_at:
                self.completed_at = datetime.utcnow()
        elif self.failed_tasks > 0 and (self.completed_tasks + self.failed_tasks) == self.total_tasks:
            self.status = BatchStatus.PARTIAL if self.completed_tasks > 0 else BatchStatus.FAILED
            if not self.completed_at:
                self.completed_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'batch_id': self.batch_id,
            'job_type': self.job_type,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'metadata': self.metadata,
            'task_count': len(self.tasks)
        }


class BatchProcessor(ABC):
    """Abstract base class for batch processors."""
    
    @abstractmethod
    async def process_task(self, task: BatchTask) -> Any:
        """Process a single task and return the result."""
        pass
    
    @abstractmethod
    def get_processor_type(self) -> str:
        """Get the processor type identifier."""
        pass


class RecommendationBatchProcessor(BatchProcessor):
    """Batch processor for generating recommendations."""
    
    def __init__(self, recommender_service: Any, max_recommendations: int = 10):
        self.recommender_service = recommender_service
        self.max_recommendations = max_recommendations
    
    async def process_task(self, task: BatchTask) -> Any:
        """Process a recommendation task."""
        try:
            input_data = task.input_data
            user_id = input_data.get('user_id')
            n_recommendations = input_data.get('n_recommendations', self.max_recommendations)
            recommendation_type = input_data.get('type', 'hybrid')
            
            # Generate recommendations
            if hasattr(self.recommender_service, 'get_recommendations_async'):
                recommendations = await self.recommender_service.get_recommendations_async(
                    user_id=user_id,
                    n_recommendations=n_recommendations,
                    recommendation_type=recommendation_type
                )
            else:
                # Fallback to sync method
                recommendations = await asyncio.to_thread(
                    self.recommender_service.get_recommendations,
                    user_id=user_id,
                    n_recommendations=n_recommendations
                )
            
            return {
                'user_id': user_id,
                'recommendations': recommendations,
                'recommendation_type': recommendation_type,
                'count': len(recommendations) if recommendations else 0
            }
            
        except Exception as e:
            logger.error(f"Recommendation task failed for user {input_data.get('user_id')}: {str(e)}")
            raise
    
    def get_processor_type(self) -> str:
        return "recommendations"


class UserAnalyticsBatchProcessor(BatchProcessor):
    """Batch processor for user analytics."""
    
    def __init__(self, analytics_service: Any):
        self.analytics_service = analytics_service
    
    async def process_task(self, task: BatchTask) -> Any:
        """Process a user analytics task."""
        try:
            input_data = task.input_data
            user_id = input_data.get('user_id')
            analytics_type = input_data.get('analytics_type', 'profile')
            
            # Generate user analytics
            if analytics_type == 'profile':
                result = await self._generate_user_profile(user_id)
            elif analytics_type == 'preferences':
                result = await self._analyze_user_preferences(user_id)
            elif analytics_type == 'behavior':
                result = await self._analyze_user_behavior(user_id)
            else:
                raise ValueError(f"Unknown analytics type: {analytics_type}")
            
            return {
                'user_id': user_id,
                'analytics_type': analytics_type,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"User analytics task failed for user {input_data.get('user_id')}: {str(e)}")
            raise
    
    async def _generate_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Generate user profile analytics."""
        # This would integrate with your actual analytics service
        return {
            'user_id': user_id,
            'profile_score': 0.85,
            'preferences': ['fiction', 'mystery', 'science'],
            'activity_level': 'high'
        }
    
    async def _analyze_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Analyze user preferences."""
        return {
            'user_id': user_id,
            'top_genres': ['fiction', 'mystery'],
            'preferred_authors': ['Author 1', 'Author 2'],
            'reading_frequency': 'weekly'
        }
    
    async def _analyze_user_behavior(self, user_id: str) -> Dict[str, Any]:
        """Analyze user behavior patterns."""
        return {
            'user_id': user_id,
            'session_duration_avg': 25.5,
            'pages_per_session': 12,
            'engagement_score': 0.78
        }
    
    def get_processor_type(self) -> str:
        return "user_analytics"


class BatchProcessingEngine:
    """
    Main batch processing engine.
    
    Features:
    - Concurrent task processing
    - Progress tracking
    - Error handling and retry logic
    - Rate limiting
    - Resource management
    """
    
    def __init__(self, 
                 max_concurrent_tasks: int = 10,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 job_retention_hours: int = 24):
        
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.job_retention_hours = job_retention_hours
        
        self.processors: Dict[str, BatchProcessor] = {}
        self.active_jobs: Dict[str, BatchJob] = {}
        self.job_history: List[BatchJob] = []
        
        # Task queue and workers
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.running = False
        
        # Statistics
        self.stats = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'average_task_time': 0.0
        }
    
    def register_processor(self, processor: BatchProcessor):
        """Register a batch processor."""
        processor_type = processor.get_processor_type()
        self.processors[processor_type] = processor
        logger.info(f"Registered batch processor: {processor_type}")
    
    async def start(self):
        """Start the batch processing engine."""
        if self.running:
            logger.warning("Batch processing engine already running")
            return
        
        self.running = True
        
        # Start worker tasks
        for i in range(self.max_concurrent_tasks):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_old_jobs())
        self.workers.append(cleanup_task)
        
        logger.info(f"Started batch processing engine with {self.max_concurrent_tasks} workers")
    
    async def stop(self):
        """Stop the batch processing engine."""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("Stopped batch processing engine")
    
    async def submit_batch_job(self, job_type: str, tasks_data: List[Any], 
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """Submit a new batch job."""
        if job_type not in self.processors:
            raise ValueError(f"No processor registered for job type: {job_type}")
        
        # Create batch job
        batch_id = str(uuid.uuid4())
        tasks = []
        
        for i, task_data in enumerate(tasks_data):
            task = BatchTask(
                task_id=f"{batch_id}-{i}",
                input_data=task_data
            )
            tasks.append(task)
        
        job = BatchJob(
            batch_id=batch_id,
            job_type=job_type,
            tasks=tasks,
            metadata=metadata or {}
        )
        
        self.active_jobs[batch_id] = job
        self.stats['total_jobs'] += 1
        self.stats['total_tasks'] += len(tasks)
        
        # Queue all tasks
        for task in tasks:
            await self.task_queue.put((job_type, batch_id, task))
        
        logger.info(f"Submitted batch job {batch_id} with {len(tasks)} tasks")
        return batch_id
    
    async def get_job_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a batch job."""
        if batch_id in self.active_jobs:
            job = self.active_jobs[batch_id]
            job.update_progress()
            return job.to_dict()
        
        # Check job history
        for job in self.job_history:
            if job.batch_id == batch_id:
                return job.to_dict()
        
        return None
    
    async def get_job_results(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get the results of a completed batch job."""
        job_status = await self.get_job_status(batch_id)
        if not job_status:
            return None
        
        job = self.active_jobs.get(batch_id)
        if not job:
            # Check history
            for historical_job in self.job_history:
                if historical_job.batch_id == batch_id:
                    job = historical_job
                    break
        
        if not job:
            return None
        
        results = {
            'batch_id': batch_id,
            'status': job_status,
            'results': [],
            'errors': []
        }
        
        for task in job.tasks:
            if task.status == TaskStatus.COMPLETED:
                results['results'].append({
                    'task_id': task.task_id,
                    'input': task.input_data,
                    'output': task.output_data,
                    'execution_time_ms': task.execution_time_ms
                })
            elif task.status == TaskStatus.FAILED:
                results['errors'].append({
                    'task_id': task.task_id,
                    'input': task.input_data,
                    'error': task.error_message,
                    'retry_count': task.retry_count
                })
        
        return results
    
    async def cancel_job(self, batch_id: str) -> bool:
        """Cancel a batch job."""
        if batch_id not in self.active_jobs:
            return False
        
        job = self.active_jobs[batch_id]
        job.status = BatchStatus.CANCELLED
        
        # Update pending tasks
        for task in job.tasks:
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.FAILED
                task.error_message = "Job cancelled"
        
        logger.info(f"Cancelled batch job {batch_id}")
        return True
    
    async def get_engine_stats(self) -> Dict[str, Any]:
        """Get batch processing engine statistics."""
        active_jobs_count = len(self.active_jobs)
        queue_size = self.task_queue.qsize()
        
        # Calculate success rates
        total_jobs = self.stats['total_jobs']
        total_tasks = self.stats['total_tasks']
        
        job_success_rate = (self.stats['completed_jobs'] / total_jobs) if total_jobs > 0 else 0
        task_success_rate = (self.stats['completed_tasks'] / total_tasks) if total_tasks > 0 else 0
        
        return {
            'engine_status': 'running' if self.running else 'stopped',
            'active_workers': len([w for w in self.workers if not w.done()]),
            'active_jobs': active_jobs_count,
            'queue_size': queue_size,
            'registered_processors': list(self.processors.keys()),
            'statistics': {
                **self.stats,
                'job_success_rate': job_success_rate,
                'task_success_rate': task_success_rate
            }
        }
    
    async def get_active_jobs_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all active jobs."""
        summaries = []
        
        for job in self.active_jobs.values():
            job.update_progress()
            summaries.append({
                'batch_id': job.batch_id,
                'job_type': job.job_type,
                'status': job.status.value,
                'progress': job.progress,
                'total_tasks': job.total_tasks,
                'completed_tasks': job.completed_tasks,
                'failed_tasks': job.failed_tasks,
                'created_at': job.created_at.isoformat(),
                'started_at': job.started_at.isoformat() if job.started_at else None
            })
        
        return summaries
    
    # Private methods
    
    async def _worker(self, worker_name: str):
        """Worker task that processes tasks from the queue."""
        logger.info(f"Started batch worker: {worker_name}")
        
        while self.running:
            try:
                # Get task from queue with timeout
                try:
                    job_type, batch_id, task = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Check if job is still active
                if batch_id not in self.active_jobs:
                    continue
                
                job = self.active_jobs[batch_id]
                
                # Skip if job is cancelled
                if job.status == BatchStatus.CANCELLED:
                    continue
                
                # Process the task
                await self._process_task(job_type, batch_id, task)
                
                # Update job progress
                job.update_progress()
                
                # Move completed jobs to history
                if job.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.PARTIAL]:
                    self._move_job_to_history(batch_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {str(e)}")
        
        logger.info(f"Stopped batch worker: {worker_name}")
    
    async def _process_task(self, job_type: str, batch_id: str, task: BatchTask):
        """Process a single task."""
        processor = self.processors[job_type]
        
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.utcnow()
        
        # Set job as started if not already
        job = self.active_jobs[batch_id]
        if job.status == BatchStatus.PENDING:
            job.status = BatchStatus.RUNNING
            job.started_at = datetime.utcnow()
        
        start_time = time.time()
        
        try:
            result = await processor.process_task(task)
            
            task.output_data = result
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.utcnow()
            task.execution_time_ms = (time.time() - start_time) * 1000
            
            # Update statistics
            self.stats['completed_tasks'] += 1
            self._update_average_task_time(task.execution_time_ms)
            
            logger.debug(f"Completed task {task.task_id} in {task.execution_time_ms:.2f}ms")
            
        except Exception as e:
            task.error_message = str(e)
            task.end_time = datetime.utcnow()
            task.execution_time_ms = (time.time() - start_time) * 1000
            
            # Retry logic
            if task.retry_count < self.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                
                # Re-queue the task after delay
                await asyncio.sleep(self.retry_delay * (2 ** task.retry_count))  # Exponential backoff
                await self.task_queue.put((job_type, batch_id, task))
                
                logger.warning(f"Retrying task {task.task_id} (attempt {task.retry_count + 1})")
            else:
                task.status = TaskStatus.FAILED
                self.stats['failed_tasks'] += 1
                
                logger.error(f"Task {task.task_id} failed after {self.max_retries} retries: {str(e)}")
    
    def _move_job_to_history(self, batch_id: str):
        """Move completed job to history."""
        if batch_id in self.active_jobs:
            job = self.active_jobs[batch_id]
            self.job_history.append(job)
            del self.active_jobs[batch_id]
            
            # Update job statistics
            if job.status == BatchStatus.COMPLETED:
                self.stats['completed_jobs'] += 1
            else:
                self.stats['failed_jobs'] += 1
            
            logger.info(f"Moved job {batch_id} to history with status {job.status.value}")
    
    def _update_average_task_time(self, execution_time_ms: float):
        """Update running average of task execution time."""
        completed_tasks = self.stats['completed_tasks']
        current_avg = self.stats['average_task_time']
        
        # Running average calculation
        self.stats['average_task_time'] = (
            (current_avg * (completed_tasks - 1) + execution_time_ms) / completed_tasks
        )
    
    async def _cleanup_old_jobs(self):
        """Cleanup old jobs from history."""
        while self.running:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=self.job_retention_hours)
                
                # Remove old jobs from history
                self.job_history = [
                    job for job in self.job_history
                    if job.completed_at and job.completed_at >= cutoff_time
                ]
                
                await asyncio.sleep(3600)  # Run cleanup every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Job cleanup error: {str(e)}")
                await asyncio.sleep(3600)


# Helper functions

def create_recommendation_batch(user_ids: List[int], 
                              n_recommendations: int = 10,
                              recommendation_type: str = "hybrid") -> List[Dict[str, Any]]:
    """Create batch tasks for recommendations."""
    return [
        {
            'user_id': user_id,
            'n_recommendations': n_recommendations,
            'type': recommendation_type
        }
        for user_id in user_ids
    ]


def create_user_analytics_batch(user_ids: List[int], 
                               analytics_type: str = "profile") -> List[Dict[str, Any]]:
    """Create batch tasks for user analytics."""
    return [
        {
            'user_id': user_id,
            'analytics_type': analytics_type
        }
        for user_id in user_ids
    ]


async def setup_batch_processing_engine(recommender_service: Any = None,
                                       analytics_service: Any = None,
                                       max_concurrent_tasks: int = 10) -> BatchProcessingEngine:
    """Setup batch processing engine with default processors."""
    engine = BatchProcessingEngine(max_concurrent_tasks=max_concurrent_tasks)
    
    # Register processors
    if recommender_service:
        engine.register_processor(RecommendationBatchProcessor(recommender_service))
    
    if analytics_service:
        engine.register_processor(UserAnalyticsBatchProcessor(analytics_service))
    
    # Start the engine
    await engine.start()
    
    return engine


# Alias for backward compatibility
BatchProcessor = BatchProcessingEngine
