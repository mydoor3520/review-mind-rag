class ReviewMindError(Exception):
    pass


class ConfigurationError(ReviewMindError):
    pass


class APIKeyNotFoundError(ConfigurationError):
    pass


class VectorStoreError(ReviewMindError):
    pass


class CollectionNotFoundError(VectorStoreError):
    pass


class IndexingError(VectorStoreError):
    pass


class DocumentProcessingError(ReviewMindError):
    pass


class InvalidReviewError(DocumentProcessingError):
    pass


class PreprocessingError(DocumentProcessingError):
    pass


class RAGChainError(ReviewMindError):
    pass


class RetrievalError(RAGChainError):
    pass


class GenerationError(RAGChainError):
    pass


class DataLoaderError(ReviewMindError):
    pass


class CategoryNotFoundError(DataLoaderError):
    pass


class DatasetLoadError(DataLoaderError):
    pass
