
'''
VectorMemory Class
Handles permanent storage and retrieval of embeddings and associated data
Author: Prometheus AI
Date: 2025-02-11
'''

import numpy as np
from typing import Dict, List, Any
import faiss
import pickle
import os

class VectorMemory:
    def __init__(self, dimension: int = 768, index_path: str = 'memory/vector_store'):
        self.dimension = dimension
        self.index_path = index_path
        self.index = faiss.IndexFlatL2(dimension)
        self.data_store = {}
        self.load_index()
    
    def load_index(self):
        if os.path.exists(f"{self.index_path}/faiss.index"):
            self.index = faiss.read_index(f"{self.index_path}/faiss.index")
            with open(f"{self.index_path}/data_store.pkl", 'rb') as f:
                self.data_store = pickle.load(f)
    
    def save_index(self):
        os.makedirs(self.index_path, exist_ok=True)
        faiss.write_index(self.index, f"{self.index_path}/faiss.index")
        with open(f"{self.index_path}/data_store.pkl", 'wb') as f:
            pickle.dump(self.data_store, f)
    
    def add_memory(self, vector: np.ndarray, data: Dict[str, Any], metadata: Dict[str, Any]):
        vector_id = self.index.ntotal
        self.index.add(vector.reshape(1, -1))
        self.data_store[vector_id] = {
            'data': data,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }
        self.save_index()
        return vector_id
    
    def search(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        distances, indices = self.index.search(query_vector.reshape(1, -1), k)
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx != -1:
                result = self.data_store[int(idx)].copy()
                result['distance'] = float(distance)
                results.append(result)
        return results

    def update_memory(self, vector_id: int, new_data: Dict[str, Any]):
        if vector_id in self.data_store:
            self.data_store[vector_id]['data'].update(new_data)
            self.data_store[vector_id]['metadata']['last_updated'] = datetime.now().isoformat()
            self.save_index()
            return True
        return False
