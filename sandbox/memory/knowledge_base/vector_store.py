
import numpy as np
from typing import Dict, List, Any, Optional
import json
import os

class VectorStore:
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self.vectors = {}
        self.metadata = {}
        
    def store(self, key: str, vector: List[float], metadata: Optional[Dict] = None):
        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch. Expected {self.dimension}, got {len(vector)}")
        self.vectors[key] = np.array(vector)
        if metadata:
            self.metadata[key] = metadata
            
    def retrieve(self, key: str) -> Dict[str, Any]:
        if key not in self.vectors:
            raise KeyError(f"Key {key} not found in vector store")
        return {
            'vector': self.vectors[key].tolist(),
            'metadata': self.metadata.get(key, {})
        }
        
    def search(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        if len(query_vector) != self.dimension:
            raise ValueError(f"Query vector dimension mismatch")
        
        scores = []
        query_array = np.array(query_vector)
        
        for key, vector in self.vectors.items():
            similarity = np.dot(query_array, vector) / (np.linalg.norm(query_array) * np.linalg.norm(vector))
            scores.append((key, similarity))
            
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for key, score in scores[:k]:
            results.append({
                'key': key,
                'score': float(score),
                'vector': self.vectors[key].tolist(),
                'metadata': self.metadata.get(key, {})
            })
        
        return results
        
    def save(self, filepath: str):
        data = {
            'dimension': self.dimension,
            'vectors': {k: v.tolist() for k, v in self.vectors.items()},
            'metadata': self.metadata
        }
        with open(filepath, 'w') as f:
            json.dump(data, f)
            
    @classmethod
    def load(cls, filepath: str) -> 'VectorStore':
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        store = cls(dimension=data['dimension'])
        store.vectors = {k: np.array(v) for k, v in data['vectors'].items()}
        store.metadata = data['metadata']
        return store
