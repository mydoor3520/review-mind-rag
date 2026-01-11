"""Review Mind RAG 메인 대시보드"""

import streamlit as st
from pathlib import Path
import sys
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="Review Mind RAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def get_system_status() -> Dict[str, Any]:
    """시스템 상태를 확인합니다"""
    from pathlib import Path

    status = {
        "vectorstore_ready": False,
        "document_count": 0,
        "collection_name": "N/A",
        "category_counts": {},
        "error": None
    }

    try:
        from src.config import config

        chroma_path = Path("./chroma_db")
        if chroma_path.exists() and (chroma_path / "chroma.sqlite3").exists():
            sqlite_size = (chroma_path / "chroma.sqlite3").stat().st_size
            estimated_docs = sqlite_size // 3000

            status["vectorstore_ready"] = True
            status["document_count"] = estimated_docs
            status["collection_name"] = "reviews"

            num_categories = len(config.data.categories)
            for category in config.data.categories:
                status["category_counts"][category] = estimated_docs // num_categories
        else:
            status["vectorstore_ready"] = False

    except Exception as e:
        status["error"] = str(e)

    return status


st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<p class="main-header">🧠 Review Mind RAG</p>',
    unsafe_allow_html=True
)
st.markdown(
    '<p class="sub-header">RAG 기반 이커머스 리뷰 분석 시스템</p>',
    unsafe_allow_html=True
)

with st.sidebar:
    st.markdown("### 📊 시스템 상태")

    status = get_system_status()

    if status["vectorstore_ready"]:
        st.success("✅ 서비스 정상")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("리뷰 수", f"{status['document_count']:,}")
        with col2:
            category_counts = status.get("category_counts", {})
            total_categories = len(
                [count for count in category_counts.values() if count > 0]
            )
            st.metric("카테고리", total_categories)
    else:
        st.error("❌ 서비스 점검 중")

    st.markdown("---")
    st.markdown("### 📚 메뉴")
    st.markdown("""
    - **Search**: 상품 검색
    - **QA Chat**: 리뷰 질문
    - **Summary**: 리뷰 요약
    - **Compare**: 상품 비교
    """)

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 🔍 상품 검색")
    st.markdown("카테고리별로 상품을 검색하고 리뷰를 확인하세요.")
    if st.button("검색하기", key="btn_search"):
        st.switch_page("pages/1_Search.py")

with col2:
    st.markdown("### 💬 리뷰 QA")
    st.markdown("리뷰에 대해 자연어로 질문하고 답변을 받으세요.")
    if st.button("질문하기", key="btn_qa"):
        st.switch_page("pages/2_QA_Chat.py")

with col3:
    st.markdown("### 📊 리뷰 요약")
    st.markdown("상품별 리뷰를 자동으로 요약하고 분석합니다.")
    if st.button("요약 보기", key="btn_summary"):
        st.switch_page("pages/3_Summary.py")

with col4:
    st.markdown("### ⚖️ 상품 비교")
    st.markdown("두 상품의 리뷰를 비교 분석합니다.")
    if st.button("비교하기", key="btn_compare"):
        st.switch_page("pages/4_Compare.py")

st.markdown("---")

with st.expander("지원 카테고리", expanded=False):
    st.markdown("""
    | 카테고리 | 설명 |
    |----------|------|
    | Electronics | 전자제품 (이어폰, 스피커, 케이블 등) |
    | Appliances | 가전제품 (에어프라이어, 청소기 등) |
    | Beauty | 뷰티/화장품 |
    | Home | 가구/주방용품 |
    """)

st.markdown(
    '<p style="text-align: center; color: #888;">Review Mind RAG | '
    'Powered by LangChain + ChromaDB</p>',
    unsafe_allow_html=True
)
