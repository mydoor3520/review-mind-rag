"""리뷰 요약 페이지"""

import streamlit as st
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="리뷰 요약 - Review Mind RAG",
    page_icon="📊",
    layout="wide"
)

st.title("📊 리뷰 요약")
st.markdown("상품별 리뷰를 자동으로 요약하고 감성을 분석합니다.")


@st.cache_resource
def get_vectorstore():
    try:
        from src.rag.vectorstore import ReviewVectorStore
        return ReviewVectorStore(), None
    except Exception as e:
        return None, str(e)


@st.cache_resource
def get_summarizer():
    try:
        from src.analysis.summarizer import ReviewSummarizer
        return ReviewSummarizer(), None
    except Exception as e:
        return None, str(e)


@st.cache_resource
def get_sentiment_analyzer():
    try:
        from src.analysis.sentiment import SentimentAnalyzer
        return SentimentAnalyzer(), None
    except Exception as e:
        return None, str(e)


def search_product_reviews(
    product_id: str, k: int = 30
) -> Tuple[List[Any], Optional[str]]:
    vectorstore, error = get_vectorstore()
    if vectorstore is None:
        return [], error

    try:
        results = vectorstore.similarity_search(
            query=f"product {product_id}",
            k=k,
            filter={"product_id": product_id}
        )
        return results, None
    except Exception as e:
        return [], str(e)


def generate_summary(
    documents: List[Any]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    summarizer, error = get_summarizer()
    if summarizer is None:
        return None, error

    try:
        result = summarizer.summarize(documents)
        return result, None
    except Exception as e:
        return None, str(e)


def extract_pros_cons(
    documents: List[Any]
) -> Tuple[Optional[Dict[str, List[str]]], Optional[str]]:
    summarizer, error = get_summarizer()
    if summarizer is None:
        return None, error

    try:
        result = summarizer.extract_pros_cons(documents)
        return result, None
    except Exception as e:
        return None, str(e)


def analyze_sentiment(
    documents: List[Any]
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    analyzer, error = get_sentiment_analyzer()
    if analyzer is None:
        return None, error

    try:
        result = analyzer.analyze_documents(documents)
        return result, None
    except Exception as e:
        return None, str(e)


with st.sidebar:
    st.markdown("### 📊 시스템 상태")
    vectorstore, vs_error = get_vectorstore()
    summarizer, sum_error = get_summarizer()
    analyzer, an_error = get_sentiment_analyzer()

    if vectorstore:
        stats = vectorstore.get_collection_stats()
        st.success(f"✅ VectorStore ({stats['document_count']:,} 리뷰)")
    else:
        st.error(f"❌ VectorStore: {vs_error}")

    if summarizer:
        st.success("✅ Summarizer 준비")
    else:
        st.error(f"❌ Summarizer: {sum_error}")

    if analyzer:
        st.success("✅ SentimentAnalyzer 준비")
    else:
        st.error(f"❌ Analyzer: {an_error}")

    st.markdown("---")
    st.markdown("### ⚙️ 설정")
    max_reviews = st.slider("분석할 최대 리뷰 수", min_value=10, max_value=50, value=30)

product_id = st.text_input("상품 ID 입력", placeholder="ASIN 또는 상품 ID...")

if st.button("📊 요약 생성", type="primary"):
    if product_id:
        with st.spinner("리뷰를 분석하고 있습니다..."):
            documents, search_error = search_product_reviews(product_id, k=max_reviews)

            if search_error:
                st.error(f"검색 오류: {search_error}")
            elif not documents:
                st.warning(f"상품 ID '{product_id}'에 대한 리뷰를 찾을 수 없습니다.")
            else:
                st.success(f"{len(documents)}개의 리뷰를 찾았습니다.")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### ✅ 장점 / ❌ 단점")
                    pros_cons, pc_error = extract_pros_cons(documents)

                    if pc_error:
                        st.error(f"장단점 추출 오류: {pc_error}")
                    elif pros_cons:
                        pros_col, cons_col = st.columns(2)
                        with pros_col:
                            st.markdown("**✅ 장점**")
                            for pro in pros_cons.get("pros", []):
                                st.markdown(f"- {pro}")
                        with cons_col:
                            st.markdown("**❌ 단점**")
                            for con in pros_cons.get("cons", []):
                                st.markdown(f"- {con}")

                with col2:
                    st.markdown("### 📈 감성 분석")
                    sentiment_result, sent_error = analyze_sentiment(documents)

                    if sent_error:
                        st.error(f"감성 분석 오류: {sent_error}")
                    elif sentiment_result:
                        dist = sentiment_result["distribution"]

                        metric_col1, metric_col2, metric_col3 = st.columns(3)
                        with metric_col1:
                            st.metric("😊 긍정", f"{dist['positive']['percentage']}%")
                        with metric_col2:
                            st.metric("😐 중립", f"{dist['neutral']['percentage']}%")
                        with metric_col3:
                            st.metric("😞 부정", f"{dist['negative']['percentage']}%")

                        avg_rating = sentiment_result['average_rating']
                        st.metric("⭐ 평균 평점", f"{avg_rating}점")

                st.markdown("---")
                st.markdown("### 📝 종합 요약")
                summary_result, sum_error = generate_summary(documents)

                if sum_error:
                    st.error(f"요약 생성 오류: {sum_error}")
                elif summary_result:
                    st.markdown(summary_result["summary"])
                    review_count = summary_result['review_count']
                    total_count = summary_result.get('total_available', len(documents))
                    st.caption(f"분석된 리뷰: {review_count}개 / 총 {total_count}개")
    else:
        st.warning("상품 ID를 입력해주세요.")

st.markdown("---")

with st.expander("💡 사용 팁", expanded=False):
    st.markdown("""
    **상품 ID 찾기:**
    - Search 페이지에서 검색 후 상품 ID 확인
    - Amazon ASIN 형식 (예: B09V3KXJPB)

    **분석 내용:**
    - **장단점**: LLM이 리뷰에서 주요 장점과 단점을 추출
    - **감성 분석**: 평점 기반 긍정/중립/부정 비율 계산
    - **종합 요약**: 리뷰 전체를 분석한 상세 요약
    """)
