"""상품 비교 페이지"""

import streamlit as st
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="상품 비교 - Review Mind RAG", page_icon="⚖️", layout="wide"
)

st.title("⚖️ 상품 비교")
st.markdown("두 상품의 리뷰를 비교 분석합니다.")


@st.cache_resource
def get_qa_chain():
    try:
        from src.rag.vectorstore import ReviewVectorStore
        from src.rag.chain import ReviewQAChain

        vectorstore = ReviewVectorStore()
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
        return ReviewVectorStore(), None
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
            filter={"product_id": product_id}
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
    product_id: str, documents: List[Any], sentiment: Optional[Dict[str, Any]]
) -> None:
    if not documents:
        st.warning(f"상품 '{product_id}'의 리뷰를 찾을 수 없습니다.")
        return

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

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📦 상품 1")
    product_1 = st.text_input("상품 1 ID", placeholder="ASIN 또는 상품 ID...", key="p1")

with col2:
    st.markdown("### 📦 상품 2")
    product_2 = st.text_input("상품 2 ID", placeholder="ASIN 또는 상품 ID...", key="p2")

if st.button("⚖️ 비교 분석", type="primary"):
    if product_1 and product_2:
        if product_1 == product_2:
            st.warning("서로 다른 상품 ID를 입력해주세요.")
        else:
            with st.spinner("리뷰를 비교 분석하고 있습니다..."):
                docs_1, err_1 = get_product_reviews(product_1, k=max_reviews)
                docs_2, err_2 = get_product_reviews(product_2, k=max_reviews)

                sentiment_1 = analyze_product_sentiment(docs_1)
                sentiment_2 = analyze_product_sentiment(docs_2)

                st.markdown("---")
                st.markdown("### 📊 상품별 통계")

                stat_col1, stat_col2 = st.columns(2)

                with stat_col1:
                    st.markdown(f"**📦 상품 1: `{product_1}`**")
                    render_product_stats(product_1, docs_1, sentiment_1)

                with stat_col2:
                    st.markdown(f"**📦 상품 2: `{product_2}`**")
                    render_product_stats(product_2, docs_2, sentiment_2)

                if docs_1 and docs_2:
                    st.markdown("---")
                    st.markdown("### 📋 AI 비교 분석")

                    with st.spinner("AI가 리뷰를 분석하고 있습니다..."):
                        comparison, comp_error = compare_products(product_1, product_2)

                        if comp_error:
                            st.error(f"비교 분석 오류: {comp_error}")
                        elif comparison:
                            st.markdown(comparison["comparison"])

                            with st.expander("📄 상품 1 요약", expanded=False):
                                st.markdown(comparison["product_1"]["summary"])

                            with st.expander("📄 상품 2 요약", expanded=False):
                                st.markdown(comparison["product_2"]["summary"])
                else:
                    st.info("비교 분석을 위해서는 두 상품 모두 리뷰가 필요합니다.")
    else:
        st.warning("두 상품의 ID를 모두 입력해주세요.")

st.markdown("---")

with st.expander("💡 사용 팁", expanded=False):
    st.markdown("""
    **상품 ID 찾기:**
    - Search 페이지에서 검색 후 상품 ID 확인
    - Amazon ASIN 형식 (예: B09V3KXJPB)

    **비교 분석 내용:**
    - **통계**: 리뷰 수, 평균 평점, 감성 분포
    - **AI 분석**: LLM이 두 상품의 리뷰를 비교 분석
    - **개별 요약**: 각 상품의 상세 요약 제공
    """)
