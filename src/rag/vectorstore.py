"""
Vector Store 관리 모듈

Chroma DB를 사용하여 리뷰 임베딩을 저장하고 관리합니다.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm


class ReviewVectorStore:
    """
    리뷰 Vector Store 관리자
    
    Chroma DB를 사용하여 리뷰 임베딩을 저장하고 검색합니다.
    """
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "reviews",
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        :param persist_directory: Chroma DB 저장 경로
        :param collection_name: 컬렉션 이름
        :param embedding_model: OpenAI 임베딩 모델
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # OpenAI Embeddings 초기화
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        
        # Chroma 인스턴스 (lazy initialization)
        self._vectorstore: Optional[Chroma] = None
    
    @property
    def vectorstore(self) -> Chroma:
        """Chroma 인스턴스 반환 (없으면 생성)"""
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
        """
        문서들을 Vector Store에 추가합니다.
        
        :param documents: LangChain Document 리스트
        :param batch_size: 배치 크기
        :param show_progress: 진행률 표시 여부
        :return: 추가된 문서 수
        """
        total = len(documents)
        
        if show_progress:
            pbar = tqdm(total=total, desc="Adding documents to vector store")
        
        added = 0
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            self.vectorstore.add_documents(batch)
            added += len(batch)
            
            if show_progress:
                pbar.update(len(batch))
        
        if show_progress:
            pbar.close()
        
        print(f"Added {added} documents to vector store")
        return added
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        유사도 검색을 수행합니다.
        
        :param query: 검색 쿼리
        :param k: 반환할 문서 수
        :param filter: 메타데이터 필터
        :return: 검색된 Document 리스트
        """
        return self.vectorstore.similarity_search(
            query,
            k=k,
            filter=filter
        )
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """
        유사도 점수와 함께 검색을 수행합니다.
        
        :param query: 검색 쿼리
        :param k: 반환할 문서 수
        :param filter: 메타데이터 필터
        :return: (Document, score) 튜플 리스트
        """
        return self.vectorstore.similarity_search_with_score(
            query,
            k=k,
            filter=filter
        )
    
    def get_retriever(
        self,
        search_type: str = "similarity",
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ):
        """
        LangChain Retriever 인스턴스를 반환합니다.
        
        :param search_type: 검색 타입 (similarity, mmr)
        :param k: 반환할 문서 수
        :param filter: 메타데이터 필터
        :return: Retriever 인스턴스
        """
        search_kwargs = {"k": k}
        if filter:
            search_kwargs["filter"] = filter
        
        return self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
    
    def get_collection_stats(self) -> Dict:
        """
        컬렉션 통계를 반환합니다.
        
        :return: 통계 딕셔너리
        """
        collection = self.vectorstore._collection
        count = collection.count()
        
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "persist_directory": self.persist_directory,
        }
    
    def delete_collection(self) -> None:
        """컬렉션을 삭제합니다."""
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
        """
        문서들로부터 새로운 Vector Store를 생성합니다.
        
        :param documents: LangChain Document 리스트
        :param persist_directory: 저장 경로
        :param collection_name: 컬렉션 이름
        :param embedding_model: 임베딩 모델
        :return: ReviewVectorStore 인스턴스
        """
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
