"""상품 비교 페이지"""

import streamlit as st
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import config
from app.components.product_search import search_and_select_product

st.set_page_config(
    page_title="상품 비교 - Review Mind RAG", page_icon="⚖️", layout="wide"
)

st.title("⚖️ 상품 비교")
st.markdown("두 상품을 검색하여 선택하고, 리뷰를 비교 분석합니다.")


@st.cache_resource
def get_qa_chain():
    try:
        from src.rag.vectorstore import ReviewVectorStore
        from src.rag.chain import ReviewQAChain

        vectorstore = ReviewVectorStore(auto_translate=True)
        stats = vectorstore.get_collection_stats()
        if stats["document_count"] == 0:
            return None, "데이터가 로드되지 않았습니다."

        return ReviewQAChain(vectorstore=vectorstore), None
    except Exception as e:
        return None, str(e)


@st.cache_resource
def get_sentiment_analyzer():
    try:
        from src.analysis.sentiment import SentimentAnalyzer
        return SentimentAnalyzer(), None
    except Exception as e:
        return None, str(e)


@st.cache_resource
def get_vectorstore():
    try:
        from src.rag.vectorstore import ReviewVectorStore
        return ReviewVectorStore(auto_translate=True), None
    except Exception as e:
        return None, str(e)


def get_product_reviews(
    product_id: str, k: int = 20
) -> Tuple[List[Any], Optional[str]]:
    vectorstore, error = get_vectorstore()
    if vectorstore is None:
        return [], error

    try:
        results = vectorstore.similarity_search(
            query=f"product {product_id}",
            k=k,
            filter={"product_id": product_id},
            translate=False
        )
        return results, None
    except Exception as e:
        return [], str(e)


def compare_products(
    product_id_1: str, product_id_2: str
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    qa_chain, error = get_qa_chain()
    if qa_chain is None:
        return None, error

    try:
        result = qa_chain.compare_products(product_id_1, product_id_2)
        return result, None
    except Exception as e:
        return None, str(e)


def analyze_product_sentiment(documents: List[Any]) -> Optional[Dict[str, Any]]:
    analyzer, _ = get_sentiment_analyzer()
    if analyzer is None or not documents:
        return None

    try:
        return analyzer.analyze_documents(documents)
    except Exception:
        return None


def render_product_stats(
    product_id: str, product_name: Optional[str],
    documents: List[Any], sentiment: Optional[Dict[str, Any]]
) -> None:
    if not documents:
        st.warning(f"상품의 리뷰를 찾을 수 없습니다.")
        return

    if product_name:
        st.markdown(f"**{product_name[:30]}{'...' if len(product_name) > 30 else ''}**")

    st.metric("📝 리뷰 수", len(documents))

    if sentiment:
        st.metric("⭐ 평균 평점", f"{sentiment['average_rating']}점")

        dist = sentiment["distribution"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("😊", f"{dist['positive']['percentage']}%")
        with col2:
            st.metric("😐", f"{dist['neutral']['percentage']}%")
        with col3:
            st.metric("😞", f"{dist['negative']['percentage']}%")


# 사이드바
with st.sidebar:
    st.markdown("### 📊 시스템 상태")
    qa_chain, qa_error = get_qa_chain()
    if qa_chain:
        st.success("✅ 비교 시스템 준비 완료")
    else:
        st.error(f"❌ {qa_error}")

    st.markdown("---")
    st.markdown("### ⚙️ 설정")
    max_reviews = st.slider(
        "상품당 분석할 리뷰 수", min_value=5, max_value=30, value=15
    )

# 메인 영역
vectorstore, _ = get_vectorstore()
if vectorstore is None:
    st.error("VectorStore가 초기화되지 않았습니다.")
    st.stop()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📦 상품 1")
    product_1_id, product_1_name = search_and_select_product(
        vectorstore=vectorstore,
        key_prefix="compare_p1",
        label="상품 1 검색",
        placeholder="첫 번째 상품명...",
        categories=config.data.categories
    )

with col2:
    st.markdown("### 📦 상품 2")
    product_2_id, product_2_name = search_and_select_product(
        vectorstore=vectorstore,
        key_prefix="compare_p2",
        label="상품 2 검색",
        placeholder="두 번째 상품명...",
        categories=config.data.categories
    )

st.markdown("---")

# 비교 분석 버튼
if product_1_id and product_2_id:
    if product_1_id == product_2_id:
        st.warning("서로 다른 상품을 선택해주세요.")
    else:
        if st.button("⚖️ 비교 분석", type="primary", use_container_width=True):
            with st.spinner("리뷰를 비교 분석하고 있습니다..."):
                docs_1, err_1 = get_product_reviews(product_1_id, k=max_reviews)
                docs_2, err_2 = get_product_reviews(product_2_id, k=max_reviews)

                sentiment_1 = analyze_product_sentiment(docs_1)
                sentiment_2 = analyze_product_sentiment(docs_2)

                st.markdown("### 📊 상품별 통계")

                stat_col1, stat_col2 = st.columns(2)

                with stat_col1:
                    st.markdown(f"**📦 상품 1**")
                    render_product_stats(product_1_id, product_1_name, docs_1, sentiment_1)

                with stat_col2:
                    st.markdown(f"**📦 상품 2**")
                    render_product_stats(product_2_id, product_2_name, docs_2, sentiment_2)

                if docs_1 and docs_2:
                    st.markdown("---")
                    st.markdown("### 📋 AI 비교 분석")

                    with st.spinner("AI가 리뷰를 분석하고 있습니다..."):
                        comparison, comp_error = compare_products(product_1_id, product_2_id)

                        if comp_error:
                            st.error(f"비교 분석 오류: {comp_error}")
                        elif comparison:
                            st.markdown(comparison["comparison"])

                            col_sum1, col_sum2 = st.columns(2)
                            with col_sum1:
                                with st.expander("📄 상품 1 요약", expanded=False):
                                    st.markdown(comparison["product_1"]["summary"])

                            with col_sum2:
                                with st.expander("📄 상품 2 요약", expanded=False):
                                    st.markdown(comparison["product_2"]["summary"])
                else:
                    st.info("비교 분석을 위해서는 두 상품 모두 리뷰가 필요합니다.")
else:
    st.info("👆 위에서 비교할 두 상품을 각각 검색하고 선택하세요.")

st.markdown("---")

with st.expander("💡 사용 팁", expanded=False):
    st.markdown("""
    **사용 방법:**
    1. 상품 1, 상품 2 각각의 검색창에 상품명 입력
    2. 검색 버튼 클릭 또는 엔터
    3. 검색 결과에서 비교할 상품 선택
    4. "비교 분석" 버튼 클릭

    **비교 분석 내용:**
    - **통계**: 리뷰 수, 평균 평점, 감성 분포
    - **AI 분석**: LLM이 두 상품의 리뷰를 비교 분석
    - **개별 요약**: 각 상품의 상세 요약 제공
    """)
