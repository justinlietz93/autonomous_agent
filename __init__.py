
from typing import List, Dict, Any
from abc import ABC, abstractmethod

class VectorStore(ABC):
    @abstractmethod
    def add_embeddings(self, texts: List[str], metadata: List[Dict[str, Any]] = None) -> bool:
        pass
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        pass
