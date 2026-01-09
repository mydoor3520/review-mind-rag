import streamlit as st
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(page_title="상품 검색 - Review Mind RAG", page_icon="🔍", layout="wide")

st.title("🔍 상품 검색")
st.markdown("카테고리별로 상품을 검색하고 리뷰를 확인하세요.")


@st.cache_resource
def get_vectorstore():
    try:
        from src.rag.vectorstore import ReviewVectorStore
        return ReviewVectorStore()
    except Exception as e:
        st.error(f"VectorStore 초기화 실패: {e}")
        return None


def search_reviews(query: str, category: str, k: int = 10):
    vectorstore = get_vectorstore()
    if vectorstore is None:
        return []
    
    try:
        filter_dict = None
        if category and category != "전체":
            filter_dict = {"category": category}
        
        results = vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict
        )
        return results
    except Exception as e:
        st.error(f"검색 오류: {e}")
        return []


def get_collection_stats():
    vectorstore = get_vectorstore()
    if vectorstore is None:
        return None
    
    try:
        return vectorstore.get_collection_stats()
    except Exception:
        return None


with st.sidebar:
    st.markdown("### 📊 컬렉션 정보")
    stats = get_collection_stats()
    if stats:
        st.metric("총 리뷰 수", f"{stats['document_count']:,}")
        st.metric("컬렉션", stats['collection_name'])
    else:
        st.warning("데이터가 로드되지 않았습니다.")
    
    st.markdown("---")
    st.markdown("### ⚙️ 검색 설정")
    result_count = st.slider("검색 결과 수", min_value=5, max_value=50, value=10)

col1, col2 = st.columns([3, 1])

with col1:
    search_query = st.text_input("검색어 입력", placeholder="상품명 또는 키워드...")

with col2:
    category = st.selectbox(
        "카테고리",
        ["전체", "Electronics", "Appliances", "Beauty", "Home"]
    )

if st.button("🔍 검색", type="primary"):
    if search_query:
        with st.spinner("검색 중..."):
            results = search_reviews(search_query, category, k=result_count)
            
            if results:
                st.success(f"{len(results)}개의 리뷰를 찾았습니다.")
                st.session_state["search_results"] = results
            else:
                st.warning("검색 결과가 없습니다. 데이터가 로드되었는지 확인해주세요.")
                st.session_state["search_results"] = []
    else:
        st.warning("검색어를 입력해주세요.")

st.markdown("---")
st.markdown("### 검색 결과")

if "search_results" in st.session_state and st.session_state["search_results"]:
    for i, (doc, score) in enumerate(st.session_state["search_results"], 1):
        metadata = doc.metadata
        rating = metadata.get("rating", "N/A")
        sentiment = metadata.get("sentiment", "neutral")
        category_name = metadata.get("category", "Unknown")
        product_id = metadata.get("product_id", "Unknown")
        
        sentiment_emoji = {"positive": "😊", "negative": "😞", "neutral": "😐"}.get(sentiment, "😐")
        
        with st.expander(f"**{i}. [{category_name}] ⭐ {rating}점 {sentiment_emoji}** (유사도: {1-score:.2%})", expanded=(i <= 3)):
            st.markdown(f"**상품 ID:** `{product_id}`")
            st.markdown("**리뷰 내용:**")
            st.markdown(f"> {doc.page_content}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"평점: {rating}점")
            with col2:
                st.caption(f"감성: {sentiment}")
            with col3:
                st.caption(f"카테고리: {category_name}")
else:
    st.markdown("*검색어를 입력하고 검색 버튼을 클릭하세요.*")
