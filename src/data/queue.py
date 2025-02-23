from queue import Queue
from typing import Any, Optional
from datetime import datetime

class LogQueue:
    def __init__(self, maxsize: int = 1000):
        self.queue = Queue(maxsize=maxsize)
        
    def put(self, message: str, is_error: bool = False):
        try:
            log_entry = {
                'message': message,
                'is_error': is_error,
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            self.queue.put(log_entry, timeout=1)
            return True
        except:
            return False
            
    def get(self, timeout: int = 1) -> Optional[dict]:
        try:
            return self.queue.get(timeout=timeout)
        except:
            return None
            
    def empty(self) -> bool:
        return self.queue.empty()
        
    def clear(self):
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except:
                break 