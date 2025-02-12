
import unittest
import time
from src.error_recovery import ErrorRecoveryManager

class TestErrorRecoveryManager(unittest.TestCase):
    def setUp(self):
        self.recovery_manager = ErrorRecoveryManager()
        
    def test_retry_success(self):
        counter = 0
        
        @self.recovery_manager.with_retry
        def succeeds_eventually():
            nonlocal counter
            counter += 1
            if counter < 2:
                raise ValueError("Temporary failure")
            return "success"
            
        result = succeeds_eventually()
        self.assertEqual(result, "success")
        self.assertEqual(counter, 2)
        
    def test_retry_exhaustion(self):
        @self.recovery_manager.with_retry
        def always_fails():
            raise ValueError("Persistent failure")
            
        with self.assertRaises(ValueError):
            always_fails()
            
    def test_checkpoint_creation(self):
        checkpoint_id = self.recovery_manager.create_checkpoint()
        self.assertIsInstance(checkpoint_id, str)
        self.assertTrue(len(checkpoint_id) > 0)
        
    def test_rollback(self):
        checkpoint_id = self.recovery_manager.create_checkpoint()
        success = self.recovery_manager.rollback_to_checkpoint(checkpoint_id)
        self.assertTrue(success)

if __name__ == '__main__':
    unittest.main()
