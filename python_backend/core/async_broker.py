import asyncio
import logging
from typing import Callable, Any
import time

class AsyncBroker:
    """
    Asynchronous Load Broker for LLM Inference.
    Prevents Ollama/GPU VRAM collapse when 1000 agents fire concurrently.
    Pipes requests through a constrained Semaphore queue.
    """
    def __init__(self, max_concurrent: int = 2):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue_size = 0
        logging.info(f"[AsyncBroker] Initialized with max {max_concurrent} concurrent LLM streams.")

    async def execute_queued(self, task_id: str, llm_func: Callable, *args, **kwargs) -> str:
        """
        Agent calls this to get LLM thought. It waits in queue if full.
        """
        self.queue_size += 1
        logging.info(f"[{task_id}] Enqueued LLM request. Queue depth: {self.queue_size}")
        
        async with self.semaphore:
            self.queue_size -= 1
            logging.info(f"[{task_id}] Executing LLM inference. Active queue: {self.queue_size}")
            
            # Simulated backoff for resilience
            retries = 3
            backoff = 2
            
            for attempt in range(retries):
                try:
                    # In a real async loop, run_in_executor allows sync code (like requests) to not block
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, lambda: llm_func(*args, **kwargs))
                    return result
                except Exception as e:
                    logging.warning(f"[{task_id}] LLM inference failed on attempt {attempt+1}: {e}")
                    if attempt < retries - 1:
                        await asyncio.sleep(backoff)
                        backoff *= 2
            
            return f"[AsyncBroker Error] Failed after {retries} retries."

# Global singleton
broker = AsyncBroker(max_concurrent=3)
