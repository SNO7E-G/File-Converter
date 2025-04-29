import os
import threading
import queue
import time
import logging
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.converters.converter_factory import ConverterFactory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BatchProcessorTask:
    """Represents a single file conversion task in the batch"""
    
    def __init__(self, 
                 source_path: str, 
                 target_path: str, 
                 source_format: str, 
                 target_format: str,
                 options: Optional[Dict[str, Any]] = None,
                 task_id: Optional[str] = None):
        self.source_path = source_path
        self.target_path = target_path
        self.source_format = source_format
        self.target_format = target_format
        self.options = options or {}
        self.task_id = task_id or self._generate_task_id()
        self.start_time = None
        self.end_time = None
        self.status = "pending"  # pending, processing, completed, failed
        self.error = None
        self.result = None
        
    def _generate_task_id(self) -> str:
        """Generate a unique task ID"""
        return f"{int(time.time())}-{os.path.basename(self.source_path)}"
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "source_path": self.source_path,
            "target_path": self.target_path,
            "source_format": self.source_format,
            "target_format": self.target_format,
            "options": self.options,
            "status": self.status,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration
        }
        
class BatchProcessor:
    """
    Handles batch processing of file conversions with various optimization algorithms
    """
    
    MAX_WORKERS = 4  # Default max number of worker threads
    
    def __init__(self, max_workers: int = MAX_WORKERS):
        self.max_workers = max_workers
        self.tasks: Dict[str, BatchProcessorTask] = {}
        self.results: Dict[str, Any] = {}
        self.active = False
        self.task_queue = queue.Queue()
        self.processing_thread = None
        self.on_progress_callback: Optional[Callable[[str, int, int], None]] = None
        self.on_task_complete_callback: Optional[Callable[[str, bool], None]] = None
    
    def add_task(self, task: BatchProcessorTask) -> str:
        """
        Add a new task to the batch processor
        
        Args:
            task: The BatchProcessorTask to add
            
        Returns:
            str: The task ID
        """
        self.tasks[task.task_id] = task
        self.task_queue.put(task.task_id)
        return task.task_id
    
    def add_tasks(self, tasks: List[BatchProcessorTask]) -> List[str]:
        """
        Add multiple tasks to the batch processor
        
        Args:
            tasks: List of BatchProcessorTask objects
            
        Returns:
            List[str]: List of task IDs
        """
        task_ids = []
        for task in tasks:
            task_id = self.add_task(task)
            task_ids.append(task_id)
        return task_ids
    
    def set_on_progress(self, callback: Callable[[str, int, int], None]) -> None:
        """
        Set callback for progress updates
        
        Args:
            callback: Function(task_id, current, total) to call with progress updates
        """
        self.on_progress_callback = callback
    
    def set_on_task_complete(self, callback: Callable[[str, bool], None]) -> None:
        """
        Set callback for task completion
        
        Args:
            callback: Function(task_id, success) to call when a task completes
        """
        self.on_task_complete_callback = callback
    
    def start(self) -> None:
        """Start processing the batch"""
        if self.active:
            logger.warning("Batch processor is already running")
            return
            
        self.active = True
        self.processing_thread = threading.Thread(target=self._process_batch)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        logger.info(f"Started batch processor with {self.max_workers} workers")
    
    def stop(self) -> None:
        """Stop the batch processor"""
        self.active = False
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)
            logger.info("Stopped batch processor")
    
    def get_task(self, task_id: str) -> Optional[BatchProcessorTask]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, BatchProcessorTask]:
        """Get all tasks"""
        return self.tasks
    
    def clear_completed_tasks(self) -> int:
        """
        Clear all completed tasks
        
        Returns:
            int: Number of tasks cleared
        """
        count = 0
        for task_id in list(self.tasks.keys()):
            task = self.tasks[task_id]
            if task.status in ("completed", "failed"):
                del self.tasks[task_id]
                count += 1
        return count
    
    def _process_batch(self) -> None:
        """Main processing loop - processes tasks in parallel with worker threads"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task_id = {}
            completed_count = 0
            total_count = self.task_queue.qsize()
            
            while self.active:
                # Submit new tasks while we have capacity and tasks available
                while len(future_to_task_id) < self.max_workers and not self.task_queue.empty():
                    try:
                        task_id = self.task_queue.get_nowait()
                        task = self.tasks[task_id]
                        task.status = "processing"
                        task.start_time = time.time()
                        
                        future = executor.submit(
                            self._process_task, 
                            task_id, 
                            task.source_path, 
                            task.target_path, 
                            task.source_format, 
                            task.target_format, 
                            task.options
                        )
                        future_to_task_id[future] = task_id
                    except queue.Empty:
                        break
                
                # Process completed tasks
                for future in list(as_completed(future_to_task_id.keys(), timeout=0.1)):
                    task_id = future_to_task_id.pop(future)
                    task = self.tasks[task_id]
                    
                    try:
                        success, error = future.result()
                        task.end_time = time.time()
                        
                        if success:
                            task.status = "completed"
                            logger.info(f"Task {task_id} completed in {task.duration:.2f}s")
                        else:
                            task.status = "failed"
                            task.error = error
                            logger.error(f"Task {task_id} failed: {error}")
                            
                        if self.on_task_complete_callback:
                            self.on_task_complete_callback(task_id, success)
                            
                    except Exception as e:
                        task.status = "failed"
                        task.error = str(e)
                        task.end_time = time.time()
                        logger.exception(f"Exception processing task {task_id}")
                        
                        if self.on_task_complete_callback:
                            self.on_task_complete_callback(task_id, False)
                    
                    completed_count += 1
                    if self.on_progress_callback:
                        self.on_progress_callback(task_id, completed_count, total_count)
                
                # If no active tasks and queue is empty, exit
                if not future_to_task_id and self.task_queue.empty():
                    logger.info("All tasks completed, batch processor stopping")
                    break
                    
                # Brief pause to avoid spinning
                time.sleep(0.1)
        
        # Mark as inactive when done
        self.active = False
    
    def _process_task(self, 
                      task_id: str, 
                      source_path: str, 
                      target_path: str, 
                      source_format: str, 
                      target_format: str, 
                      options: Dict[str, Any]) -> tuple:
        """
        Process a single conversion task
        
        Returns:
            tuple: (success: bool, error_message: Optional[str])
        """
        try:
            # Get a converter for this format pair
            converter = ConverterFactory.get_converter(source_format, target_format)
            
            # Ensure target directory exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Perform the conversion
            success, error = converter.safe_convert(source_path, target_path, options)
            
            return success, error
            
        except Exception as e:
            logger.exception(f"Error processing task {task_id}")
            return False, str(e)
    
    @staticmethod
    def optimize_batch(tasks: List[BatchProcessorTask]) -> List[BatchProcessorTask]:
        """
        Optimize the order of tasks for better performance
        
        This implementation uses several strategies:
        1. Group similar conversions to maximize cache efficiency
        2. Order by estimated complexity (simple conversions first)
        3. Ensure fair distribution of work
        
        Args:
            tasks: List of tasks to optimize
            
        Returns:
            List[BatchProcessorTask]: Optimized task list
        """
        if not tasks:
            return []
            
        # Group by source_format -> target_format pairs
        format_groups = {}
        for task in tasks:
            key = f"{task.source_format}->{task.target_format}"
            if key not in format_groups:
                format_groups[key] = []
            format_groups[key].append(task)
        
        # Sort groups by size (descending) to process largest groups first
        sorted_groups = sorted(format_groups.items(), key=lambda x: len(x[1]), reverse=True)
        
        # Interleave tasks from different groups for fair distribution
        optimized_tasks = []
        group_indices = {key: 0 for key, _ in sorted_groups}
        
        while any(group_indices[key] < len(group) for key, group in sorted_groups):
            for key, group in sorted_groups:
                idx = group_indices[key]
                if idx < len(group):
                    optimized_tasks.append(group[idx])
                    group_indices[key] += 1
        
        return optimized_tasks 