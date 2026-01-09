#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import AmazonReviewLoader
from src.data.preprocessor import ReviewPreprocessor
from src.rag.vectorstore import ReviewVectorStore, IndexingProgress, calculate_optimal_batch_size
import psutil


def get_available_memory_mb() -> float:
    return psutil.virtual_memory().available / (1024 * 1024)


def main():
    parser = argparse.ArgumentParser(description="4개 카테고리 전체 데이터 로딩 테스트")
    parser.add_argument("--limit-per-category", type=int, default=None, help="카테고리당 최대 리뷰 수")
    parser.add_argument("--batch-size", type=int, default=None, help="배치 크기 (None이면 자동 계산)")
    parser.add_argument("--collection-name", type=str, default="reviews_all", help="컬렉션 이름")
    parser.add_argument("--dry-run", action="store_true", help="실제 인덱싱 없이 로딩만 테스트")
    args = parser.parse_args()
    
    categories = ["Electronics", "Appliances", "Beauty", "Home"]
    
    print("=" * 60)
    print("4개 카테고리 전체 데이터 로딩 테스트")
    print("=" * 60)
    print(f"카테고리: {categories}")
    print(f"카테고리당 제한: {args.limit_per_category or '없음 (전체)'}")
    print(f"컬렉션: {args.collection_name}")
    print(f"사용 가능 메모리: {get_available_memory_mb():.0f} MB")
    print("=" * 60)
    
    loader = AmazonReviewLoader()
    preprocessor = ReviewPreprocessor()
    
    all_documents = []
    category_stats = {}
    
    for category in categories:
        print(f"\n[{category}] 로딩 시작...")
        
        reviews = loader.load_category(
            category=category,
            limit=args.limit_per_category,
            streaming=True
        )
        
        documents = list(preprocessor.process_reviews(reviews))
        category_stats[category] = len(documents)
        all_documents.extend(documents)
        
        print(f"[{category}] 완료: {len(documents)} 문서")
    
    print("\n" + "=" * 60)
    print("카테고리별 문서 수:")
    for cat, count in category_stats.items():
        print(f"  - {cat}: {count}")
    print(f"  총계: {len(all_documents)}")
    print("=" * 60)
    
    if args.dry_run:
        print("\n[Dry Run] 인덱싱 건너뜀")
        return
    
    batch_size = args.batch_size
    if batch_size is None:
        avg_doc_size = sum(len(doc.page_content) for doc in all_documents[:100]) // min(100, len(all_documents))
        batch_size = calculate_optimal_batch_size(
            available_memory_mb=get_available_memory_mb(),
            avg_doc_size_bytes=avg_doc_size * 4
        )
        print(f"\n자동 계산된 배치 크기: {batch_size}")
    
    print(f"\n인덱싱 시작 (batch_size={batch_size})...")
    
    vectorstore = ReviewVectorStore(collection_name=args.collection_name)
    
    def progress_callback(processed: int, total: int):
        percent = processed / total * 100
        print(f"\r진행률: {processed}/{total} ({percent:.1f}%)", end="", flush=True)
    
    stats = vectorstore.add_documents_with_stats(
        documents=all_documents,
        batch_size=batch_size,
        track_memory=True
    )
    
    print("\n\n" + "=" * 60)
    print("인덱싱 완료 통계:")
    print(f"  - 총 문서: {stats['total_documents']}")
    print(f"  - 처리 문서: {stats['processed_documents']}")
    print(f"  - 소요 시간: {stats['elapsed_time']:.2f}초")
    print(f"  - 처리 속도: {stats['documents_per_second']:.2f} docs/sec")
    print(f"  - 메모리 사용: {stats.get('memory_usage_mb', 0):.0f} MB")
    print(f"  - 피크 메모리: {stats.get('peak_memory_mb', 0):.0f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
