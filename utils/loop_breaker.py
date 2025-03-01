#!/usr/bin/env python3
"""
Loop detection and breaking utility for the autonomous agent.
Identifies when the agent is stuck in a loop and provides intervention.
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class LoopBreaker:
    """Detects and breaks agent execution loops."""
    
    def __init__(self, max_repetitions=3, window_size=5, intervention_cooldown=600):
        """
        Initialize the loop breaker.
        
        Args:
            max_repetitions: Number of repeating patterns before intervention
            window_size: Size of the pattern detection window
            intervention_cooldown: Seconds to wait before another intervention
        """
        self.max_repetitions = max_repetitions
        self.window_size = window_size
        self.intervention_cooldown = timedelta(seconds=intervention_cooldown)
        
        self.response_history = []
        self.pattern_counts = {}
        self.last_intervention = None
    
    def check_for_loops(self, response: str) -> Dict[str, Any]:
        """
        Check if the current response indicates a loop.
        
        Args:
            response: The agent's current response
            
        Returns:
            Dict with loop detection results:
            {
                "loop_detected": bool,
                "intervention_needed": bool,
                "pattern": str (if found),
                "count": int (if pattern found)
            }
        """
        result = {
            "loop_detected": False,
            "intervention_needed": False,
            "pattern": None,
            "count": 0
        }
        
        # Add fingerprint of current response
        fingerprint = self._create_fingerprint(response)
        self.response_history.append(fingerprint)
        
        # Keep history to a reasonable size
        if len(self.response_history) > self.window_size * 10:
            self.response_history = self.response_history[-self.window_size * 5:]
        
        # Look for repeating patterns
        for pattern_size in range(1, min(self.window_size, len(self.response_history))):
            pattern = tuple(self.response_history[-pattern_size:])
            
            # Count pattern occurrences in history
            count = 0
            for i in range(0, len(self.response_history) - pattern_size + 1, pattern_size):
                if tuple(self.response_history[i:i+pattern_size]) == pattern:
                    count += 1
            
            if count >= self.max_repetitions:
                result["loop_detected"] = True
                result["pattern"] = str(pattern)
                result["count"] = count
                
                # Check if we should intervene
                if self._should_intervene():
                    result["intervention_needed"] = True
                    self.last_intervention = datetime.now()
                
                break
        
        return result
    
    def get_intervention(self) -> str:
        """
        Get an intervention message to break the loop.
        
        Returns:
            Intervention message to send to the agent
        """
        return """
[SYSTEM INTERRUPT]
You appear to be stuck in a loop. Please:
1. Stop trying the same operations repeatedly
2. Try a completely different approach
3. If you're waiting for a tool, use a different tool
4. Report what you believe is causing the loop

Take a different action now.
"""
    
    def _create_fingerprint(self, response: str) -> str:
        """Create a simplified fingerprint of the response to detect patterns."""
        # Use a simple approach: first 50 chars + last 50 chars
        if len(response) <= 100:
            return response
        return response[:50] + "..." + response[-50:]
    
    def _should_intervene(self) -> bool:
        """Check if we should intervene based on cooldown period."""
        if not self.last_intervention:
            return True
        return datetime.now() - self.last_intervention > self.intervention_cooldown 