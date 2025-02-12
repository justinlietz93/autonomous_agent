
class MemoryError(Exception):
    '''Base class for memory-related exceptions'''
    pass

class StorageError(MemoryError):
    '''Raised when storage operations fail'''
    pass

class RetrievalError(MemoryError):
    '''Raised when retrieval operations fail'''
    pass

class ValidationError(MemoryError):
    '''Raised when validation fails'''
    pass

class IndexError(MemoryError):
    '''Raised when indexing operations fail'''
    pass
