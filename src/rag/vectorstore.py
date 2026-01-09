from typing import List, Optional, Dict, Any, Callable, Tuple
import time
import asyncio
import psutil
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm

from ..exceptions import IndexingError


def calculate_optimal_batch_size(
    available_memory_mb: float,
    avg_doc_size_bytes: int,
    min_batch_size: int = 10,
    max_batch_size: int = 1000,
    memory_usage_ratio: float = 0.3
) -> int:
    available_bytes = available_memory_mb * 1024 * 1024
    usable_bytes = available_bytes * memory_usage_ratio
    calculated_size = int(usable_bytes / max(avg_doc_size_bytes, 1))
    return max(min_batch_size, min(calculated_size, max_batch_size))


class IndexingProgress:
    def __init__(self, total: int):
        self.total = total
        self.processed = 0
        self._start_time: Optional[float] = None
        self._peak_memory_mb: float = 0
    
    def start(self) -> None:
        self._start_time = time.time()
        self._update_peak_memory()
    
    def update(self, count: int) -> None:
        self.processed = count
        self._update_peak_memory()
    
    def _update_peak_memory(self) -> None:
        current_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        self._peak_memory_mb = max(self._peak_memory_mb, current_memory)
    
    def get_eta(self) -> Optional[float]:
        if self._start_time is None or self.processed == 0:
            return None
        elapsed = time.time() - self._start_time
        rate = self.processed / elapsed
        remaining = self.total - self.processed
        return remaining / rate if rate > 0 else None
    
    def get_speed(self) -> Optional[float]:
        if self._start_time is None or self.processed == 0:
            return None
        elapsed = time.time() - self._start_time
        return self.processed / elapsed if elapsed > 0 else None
    
    def get_percent(self) -> float:
        return (self.processed / self.total * 100) if self.total > 0 else 0.0
    
    def get_memory_mb(self) -> float:
        return psutil.Process().memory_info().rss / (1024 * 1024)
    
    def get_peak_memory_mb(self) -> float:
        return self._peak_memory_mb


class ReviewVectorStore:
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "reviews",
        embedding_model: str = "text-embedding-3-small"
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self._vectorstore: Optional[Chroma] = None
    
    @property
    def vectorstore(self) -> Chroma:
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
        return self._vectorstore
    
    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> int:
        total = len(documents)
        pbar = tqdm(total=total, desc="Adding documents to vector store") if show_progress else None
        
        added = 0
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            self.vectorstore.add_documents(batch)
            added += len(batch)
            
            if pbar:
                pbar.update(len(batch))
        
        if pbar:
            pbar.close()
        
        print(f"Added {added} documents to vector store")
        return added
    
    def add_documents_with_progress(
        self,
        documents: List[Document],
        batch_size: int = 100,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> int:
        total = len(documents)
        added = 0
        
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            self.vectorstore.add_documents(batch)
            added += len(batch)
            
            if progress_callback:
                progress_callback(added, total)
        
        return added
    
    def add_documents_with_stats(
        self,
        documents: List[Document],
        batch_size: int = 100,
        track_memory: bool = False
    ) -> Dict[str, Any]:
        total = len(documents)
        progress = IndexingProgress(total)
        progress.start()
        
        added = 0
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            self.vectorstore.add_documents(batch)
            added += len(batch)
            progress.update(added)
        
        elapsed = time.time() - (progress._start_time or time.time())
        stats: Dict[str, Any] = {
            "total_documents": total,
            "processed_documents": added,
            "elapsed_time": elapsed,
            "documents_per_second": added / elapsed if elapsed > 0 else 0,
        }
        
        if track_memory:
            stats["memory_usage_mb"] = progress.get_memory_mb()
            stats["peak_memory_mb"] = progress.get_peak_memory_mb()
        
        return stats
    
    def add_documents_with_retry(
        self,
        documents: List[Document],
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Dict[str, Any]:
        total = len(documents)
        added = 0
        total_retries = 0
        
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            retries = 0
            
            while retries <= max_retries:
                try:
                    self.vectorstore.add_documents(batch)
                    added += len(batch)
                    break
                except Exception as e:
                    retries += 1
                    total_retries += 1
                    if retries > max_retries:
                        raise IndexingError(
                            f"배치 {i // batch_size}에서 최대 재시도 횟수 초과: {e}"
                        ) from e
                    time.sleep(retry_delay)
        
        return {
            "success": True,
            "processed": added,
            "retry_count": total_retries
        }
    
    async def add_documents_async(
        self,
        documents: List[Document],
        batch_size: int = 100,
        max_concurrent: int = 4
    ) -> Dict[str, Any]:
        total = len(documents)
        batches = [documents[i:i + batch_size] for i in range(0, total, batch_size)]
        
        semaphore = asyncio.Semaphore(max_concurrent)
        processed = 0
        
        async def process_batch(batch: List[Document]) -> int:
            nonlocal processed
            async with semaphore:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.vectorstore.add_documents, batch)
                processed += len(batch)
                return len(batch)
        
        tasks = [process_batch(batch) for batch in batches]
        await asyncio.gather(*tasks)
        
        return {
            "success": True,
            "processed": processed
        }
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        return self.vectorstore.similarity_search(query, k=k, filter=filter)
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        return self.vectorstore.similarity_search_with_score(query, k=k, filter=filter)
    
    def get_retriever(
        self,
        search_type: str = "similarity",
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ):
        search_kwargs: Dict[str, Any] = {"k": k}
        if filter:
            search_kwargs["filter"] = filter
        
        return self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
    
    def get_collection_stats(self) -> Dict[str, Any]:
        collection = self.vectorstore._collection
        count = collection.count()
        
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "persist_directory": self.persist_directory,
        }
    
    def delete_collection(self) -> None:
        self.vectorstore.delete_collection()
        self._vectorstore = None
        print(f"Deleted collection: {self.collection_name}")
    
    @classmethod
    def from_documents(
        cls,
        documents: List[Document],
        persist_directory: str = "./chroma_db",
        collection_name: str = "reviews",
        embedding_model: str = "text-embedding-3-small"
    ) -> "ReviewVectorStore":
        embeddings = OpenAIEmbeddings(model=embedding_model)
        
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name=collection_name
        )
        
        instance = cls(
            persist_directory=persist_directory,
            collection_name=collection_name,
            embedding_model=embedding_model
        )
        instance._vectorstore = vectorstore
        
        return instance
