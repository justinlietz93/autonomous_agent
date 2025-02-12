
import logging
import time

class MemoryMonitor:
    def __init__(self):
        self.logger = logging.getLogger('memory_system')
        self.metrics = {
            'operation_counts': {},
            'error_counts': {},
            'response_times': {}
        }
    
    def log_operation(self, operation: str, duration: float):
        self.metrics['operation_counts'][operation] = self.metrics['operation_counts'].get(operation, 0) + 1
        self.metrics['response_times'][operation] = self.metrics['response_times'].get(operation, []) + [duration]
        
    def log_error(self, error_type: str):
        self.metrics['error_counts'][error_type] = self.metrics['error_counts'].get(error_type, 0) + 1
