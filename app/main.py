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
    status = {
        "vectorstore_ready": False,
        "document_count": 0,
        "collection_name": "N/A",
        "category_counts": {},
        "error": None
    }

    try:
        from src.rag.vectorstore import ReviewVectorStore
        from src.config import config

        vectorstore = ReviewVectorStore()
        stats = vectorstore.get_collection_stats()
        status["vectorstore_ready"] = True
        status["document_count"] = stats.get("document_count", 0)
        status["collection_name"] = stats.get("collection_name", "reviews")

        # 카테고리별 리뷰 수 조회
        category_counts = {}
        for category in config.data.categories:
            try:
                # Chroma 필터를 사용하여 카테고리별 문서 조회
                collection = vectorstore.vectorstore._collection
                count_results = collection.get(
                    where={"category": category},
                    include=[]
                )
                category_counts[category] = (
                    len(count_results["ids"]) if count_results else 0
                )
            except Exception:
                category_counts[category] = 0

        status["category_counts"] = category_counts
    except Exception as e:
        status["error"] = str(e)

    return status


def check_api_key() -> bool:
    import os
    return bool(
        os.environ.get("OPENAI_API_KEY") or
        st.session_state.get("openai_api_key")
    )


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
        st.success("✅ VectorStore 연결됨")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("리뷰 수", f"{status['document_count']:,}")
        with col2:
            category_counts = status.get("category_counts", {})
            total_categories = len(
                [count for count in category_counts.values() if count > 0]
            )
            st.metric("카테고리", total_categories)

        # 카테고리별 상세 정보 표시
        if category_counts:
            with st.expander("카테고리별 리뷰 수"):
                for category, count in category_counts.items():
                    if count > 0:
                        st.metric(category, f"{count:,}")
    else:
        st.error("❌ VectorStore 연결 실패")
        if status["error"]:
            with st.expander("에러 상세"):
                st.code(status["error"])

    api_ready = check_api_key()
    if api_ready:
        st.success("✅ API 키 설정됨")
    else:
        st.warning("⚠️ API 키 필요")

    st.markdown("---")
    st.markdown("### ⚙️ 설정")

    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="OpenAI API 키를 입력하세요 (.env 파일에 설정 권장)"
    )

    if api_key:
        st.session_state["openai_api_key"] = api_key
        import os
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("API 키가 설정되었습니다!")
        st.rerun()

    st.markdown("---")
    st.markdown("### 🗑️ 캐시 관리")

    def get_directory_size(path: str) -> str:
        import os
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        except Exception:
            return "N/A"

        if total < 1024:
            return f"{total} B"
        elif total < 1024**2:
            return f"{total/1024:.1f} KB"
        else:
            return f"{total/1024**2:.1f} MB"

    chroma_db_path = PROJECT_ROOT / "chroma_db"
    cache_size = get_directory_size(str(chroma_db_path))
    st.metric("캐시 크기", cache_size)

    if "confirm_clear_cache" not in st.session_state:
        st.session_state.confirm_clear_cache = False

    if st.button("캐시 초기화", key="btn_clear_cache"):
        st.session_state.confirm_clear_cache = True

    if st.session_state.confirm_clear_cache:
        st.warning(
            "⚠️ 캐시를 초기화하면 모든 벡터 데이터가 삭제됩니다. "
            "계속하시겠습니까?"
        )
        col_yes, col_no = st.columns(2)

        with col_yes:
            if st.button("예, 초기화", key="btn_confirm_yes"):
                try:
                    import shutil
                    if chroma_db_path.exists():
                        shutil.rmtree(chroma_db_path)
                    st.cache_resource.clear()
                    st.session_state.confirm_clear_cache = False
                    st.success("✅ 캐시가 초기화되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"캐시 초기화 실패: {str(e)}")

        with col_no:
            if st.button("아니오, 취소", key="btn_confirm_no"):
                st.session_state.confirm_clear_cache = False
                st.rerun()

    st.markdown("---")
    st.markdown("### 📚 페이지 안내")
    st.markdown("""
    - 🔍 **Search**: 상품 검색
    - 💬 **QA Chat**: 리뷰 질문
    - 📊 **Summary**: 리뷰 요약
    - ⚖️ **Compare**: 상품 비교
    """)

st.markdown("---")

if not api_ready:
    st.warning(
        "⚠️ OpenAI API 키가 설정되지 않았습니다. "
        "사이드바에서 API 키를 입력하거나 .env 파일에 설정해주세요."
    )

if status["document_count"] == 0:
    st.info("📢 VectorStore에 데이터가 없습니다. 아래 명령어로 데이터를 로드해주세요.")
    st.code("python scripts/load_all_categories.py", language="bash")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 🔍 상품 검색")
    st.markdown("카테고리별로 상품을 검색하고 리뷰를 확인하세요.")
    if st.button("검색하기", key="btn_search"):
        st.switch_page("pages/1_🔍_Search.py")

with col2:
    st.markdown("### 💬 리뷰 QA")
    st.markdown("리뷰에 대해 자연어로 질문하고 답변을 받으세요.")
    if st.button("질문하기", key="btn_qa"):
        st.switch_page("pages/2_💬_QA_Chat.py")

with col3:
    st.markdown("### 📊 리뷰 요약")
    st.markdown("상품별 리뷰를 자동으로 요약하고 분석합니다.")
    if st.button("요약 보기", key="btn_summary"):
        st.switch_page("pages/3_📊_Summary.py")

with col4:
    st.markdown("### ⚖️ 상품 비교")
    st.markdown("두 상품의 리뷰를 비교 분석합니다.")
    if st.button("비교하기", key="btn_compare"):
        st.switch_page("pages/4_⚖️_Compare.py")

st.markdown("---")
st.markdown("### 🚀 시작하기")

with st.expander("사용 방법", expanded=True):
    st.markdown("""
    1. **API 키 설정**: `.env` 파일에 `OPENAI_API_KEY`를 설정하거나 사이드바에서 입력
    2. **데이터 로드**: 터미널에서 `python scripts/load_all_categories.py` 실행
    3. **기능 사용**: 원하는 기능을 선택하여 리뷰를 분석
    """)

with st.expander("지원 카테고리"):
    st.markdown("""
    | 카테고리 | 설명 |
    |----------|------|
    | Electronics | 전자제품 (이어폰, 스피커, 케이블 등) |
    | Appliances | 가전제품 (에어프라이어, 청소기 등) |
    | Beauty | 뷰티/화장품 |
    | Home | 가구/주방용품 |
    """)

with st.expander("데이터 로드 방법"):
    st.markdown("""
    ```bash
    # 전체 카테고리 로드 (권장)
    python scripts/load_all_categories.py

    # 또는 Python에서 직접
    from src.data.loader import AmazonReviewLoader
    from src.data.preprocessor import ReviewPreprocessor
    from src.rag.vectorstore import ReviewVectorStore

    loader = AmazonReviewLoader()
    reviews = loader.load_category("Electronics", limit=1000)

    preprocessor = ReviewPreprocessor()
    documents = list(preprocessor.process_reviews(reviews))

    vectorstore = ReviewVectorStore.from_documents(documents)
    ```
    """)

st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #888;">Review Mind RAG v0.1.0 | '
    'Built with LangChain + Chroma + Streamlit</p>',
    unsafe_allow_html=True
)
