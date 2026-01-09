import pytest

from src.exceptions import (
    ReviewMindError,
    ConfigurationError,
    APIKeyNotFoundError,
    VectorStoreError,
    IndexingError,
    DataLoaderError,
    CategoryNotFoundError,
    DatasetLoadError,
)
from src.config import OpenAIConfig


class TestExceptionHierarchy:
    def test_APIKeyNotFoundError_is_ConfigurationError(self):
        assert issubclass(APIKeyNotFoundError, ConfigurationError)
    
    def test_ConfigurationError_is_ReviewMindError(self):
        assert issubclass(ConfigurationError, ReviewMindError)
    
    def test_IndexingError_is_VectorStoreError(self):
        assert issubclass(IndexingError, VectorStoreError)
    
    def test_CategoryNotFoundError_is_DataLoaderError(self):
        assert issubclass(CategoryNotFoundError, DataLoaderError)


class TestOpenAIConfigValidation:
    def test_빈_API_키_시_APIKeyNotFoundError(self):
        config = OpenAIConfig(api_key="")
        
        with pytest.raises(APIKeyNotFoundError):
            config.validate()
    
    def test_유효한_API_키_시_True_반환(self):
        config = OpenAIConfig(api_key="sk-test-key")
        
        assert config.validate() is True


class TestCategoryNotFoundError:
    def test_에러_메시지_포함(self):
        error = CategoryNotFoundError("지원하지 않는 카테고리: Unknown")
        
        assert "Unknown" in str(error)


class TestIndexingError:
    def test_원인_체인_유지(self):
        original = ValueError("원본 에러")
        error = IndexingError("인덱싱 실패")
        error.__cause__ = original
        
        assert error.__cause__ is original
