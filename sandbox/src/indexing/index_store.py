
from typing import Dict, List, Any
import numpy as np
from datetime import datetime
import json
import os

class IndexStore:
    def __init__(self, dimension: int, index_path: str):
        self.dimension = dimension
        self.index_path = index_path
        self.index = {}
        self.load_index()
    
    def add_vector(self, key: str, vector: List[float]):
        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch. Expected {self.dimension}, got {len(vector)}")
            
        vector_norm = np.linalg.norm(vector)
        normalized_vector = np.array(vector) / vector_norm
        
        # Store normalized vector and original key
        self.index[key] = {
            'vector': normalized_vector.tolist(),
            'norm': vector_norm,
            'timestamp': datetime.now().isoformat()
        }
        self.save_index()
    
    def search(self, query_vector: List[float], k: int = 5) -> List[str]:
        if len(query_vector) != self.dimension:
            raise ValueError(f"Query vector dimension mismatch. Expected {self.dimension}, got {len(query_vector)}")
            
        # Normalize query vector
        query_norm = np.linalg.norm(query_vector)
        normalized_query = np.array(query_vector) / query_norm
        
        # Calculate similarities
        similarities = []
        for key, entry in self.index.items():
            similarity = np.dot(normalized_query, entry['vector'])
            similarities.append((key, similarity))
            
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [key for key, _ in similarities[:k]]
    
    def save_index(self):
        with open(self.index_path, 'w') as f:
            json.dump(self.index, f)
    
    def load_index(self):
        if os.path.exists(self.index_path):
            with open(self.index_path, 'r') as f:
                self.index = json.load(f)
