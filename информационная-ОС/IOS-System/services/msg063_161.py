"""
Batch Processing for Efficiency
"""

import logging
from typing import List, Dict, Callable, Any
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Batch processing for efficiency
    
    Features:
    - Automatic batching
    - Parallel processing
    - Error handling
    - Progress tracking
    
    Usage:
        processor = BatchProcessor()
        
        results = await processor.process_batch(
            items=documents,
            processor_func=index_document,
            batch_size=32
        )
    """
    
    async def process_batch(
        self,
        items: List[Any],
        processor_func: Callable,
        batch_size: int = 32,
        max_parallel: int = 4,
        on_progress: Optional[Callable] = None
    ) -> Dict:
        """
        Process items in batches
        
        Args:
            items: Items to process
            processor_func: Processing function
            batch_size: Items per batch
            max_parallel: Max parallel batches
            on_progress: Progress callback
        
        Returns:
            Processing results
        """
        
        start_time = datetime.utcnow()
        
        total = len(items)
        processed = 0
        successful = 0
        failed = 0
        errors = []
        
        # Split into batches
        batches = [
            items[i:i + batch_size]
            for i in range(0, total, batch_size)
        ]
        
        logger.info(f"Processing {total} items in {len(batches)} batches")
        
        # Process batches with concurrency limit
        semaphore = asyncio.Semaphore(max_parallel)
        
        async def process_batch_with_semaphore(batch, batch_num):
            nonlocal processed, successful, failed
            
            async with semaphore:
                logger.debug(f"Processing batch {batch_num}/{len(batches)}")
                
                batch_results = []
                
                for item in batch:
                    try:
                        result = await processor_func(item)
                        batch_results.append(result)
                        successful += 1
                    except Exception as e:
                        logger.error(f"Error processing item: {e}")
                        errors.append(str(e))
                        failed += 1
                    
                    processed += 1
                    
                    # Progress callback
                    if on_progress:
                        await on_progress(processed, total)
                
                return batch_results
        
        # Process all batches
        batch_tasks = [
            process_batch_with_semaphore(batch, i + 1)
            for i, batch in enumerate(batches)
        ]
        
        results = await asyncio.gather(*batch_tasks)
        
        # Flatten results
        all_results = [r for batch in results for r in batch]
        
        # Calculate stats
        duration = (datetime.utcnow() - start_time).total_seconds()
        throughput = total / duration if duration > 0 else 0
        
        return {
            "total": total,
            "processed": processed,
            "successful": successful,
            "failed": failed,
            "errors": errors[:10],  # First 10 errors
            "duration_seconds": round(duration, 2),
            "throughput_per_second": round(throughput, 2),
            "results": all_results
        }


# Global batch processor
batch_processor = BatchProcessor()