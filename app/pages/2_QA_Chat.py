"""리뷰 QA 채팅 페이지"""

import streamlit as st
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import config

st.set_page_config(
    page_title="리뷰 QA - Review Mind RAG",
    page_icon="💬",
    layout="wide"
)

st.title("💬 리뷰 QA 채팅")
st.markdown("리뷰에 대해 자연어로 질문하고 AI가 리뷰를 분석하여 답변합니다.")


@st.cache_resource
def get_qa_chain(_version: str = "v4") -> Tuple[Any, Optional[str]]:
    """QA Chain 인스턴스 반환 (HyDE, Reranker 지원)"""
    try:
        from src.rag.vectorstore import ReviewVectorStore
        from src.rag.chain import ReviewQAChain

        vectorstore = ReviewVectorStore()
        stats = vectorstore.get_collection_stats()
        if stats["document_count"] == 0:
            return None, "데이터가 로드되지 않았습니다."

        return ReviewQAChain(vectorstore=vectorstore, use_hyde=True, use_reranker=False), None
    except Exception as e:
        return None, str(e)


def ask_question(
    question: str,
    category: str,
    min_rating: int,
    use_reranker: bool,
    use_hyde: bool,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    qa_chain, error = get_qa_chain()
    if qa_chain is None:
        return None, error

    try:
        category_filter = None if category == "전체" else category
        rating_filter = None if min_rating == 1 else min_rating

        result = qa_chain.ask(
            question=question,
            category=category_filter,
            min_rating=rating_filter,
            use_reranker=use_reranker,
            use_hyde=use_hyde,
            chat_history=chat_history
        )
        return result, None
    except Exception as e:
        return None, str(e)


def extract_sources(source_docs: List[Any]) -> List[Dict[str, Any]]:
    sources: List[Dict[str, Any]] = []
    for doc in source_docs[:5]:
        sources.append({
            "text": doc.page_content,
            "rating": doc.metadata.get("rating", "N/A"),
            "sentiment": doc.metadata.get("sentiment", "neutral"),
            "product_id": doc.metadata.get("product_id", "Unknown")
        })
    return sources


def render_sources(sources: List[Dict[str, Any]]) -> None:
    if not sources:
        return
    with st.expander("📚 참고한 리뷰", expanded=False):
        for i, source in enumerate(sources, 1):
            sentiment_emoji = {"positive": "😊", "negative": "😞", "neutral": "😐"}.get(
                str(source.get('sentiment', 'neutral')), "😐"
            )
            st.markdown(f"""
            **리뷰 {i}** ⭐ {source.get('rating', 'N/A')}점 {sentiment_emoji}
            > {str(source.get('text', ''))[:300]}...
            """)


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("### 📊 시스템 상태")
    qa_chain, error = get_qa_chain()
    if qa_chain:
        st.success("✅ QA Chain 준비 완료")
    else:
        st.error(f"❌ {error}")

    st.markdown("---")
    st.markdown("### 🔧 필터 설정")

    categories = ["전체"] + (config.data.categories or [])
    category = st.selectbox("카테고리", categories, index=0)

    min_rating = st.slider(
        "최소 평점",
        min_value=1,
        max_value=5,
        value=1
    )

    use_hyde = st.toggle(
        "HyDE 사용",
        value=True,
        help="질문을 가상의 리뷰로 변환하여 검색 품질 향상 (권장)"
    )

    use_reranker = st.toggle(
        "Reranker 사용",
        value=False,
        help="검색 결과 재정렬로 품질 향상 (응답 시간 증가)"
    )

    st.markdown("---")
    st.markdown("### 💡 예시 질문")
    st.markdown("""
    - "이 제품 소음이 어때?"
    - "배터리 수명은 어떤가요?"
    - "가격 대비 만족도는?"
    - "내구성에 대한 평가는?"
    - "배송은 빠른 편인가요?"
    """)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant" and message.get("sources"):
            render_sources(message["sources"])

if prompt := st.chat_input("리뷰에 대해 질문하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("리뷰를 분석하고 있습니다..."):
            # 이전 대화 히스토리 전달 (sources 제외)
            chat_history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1]  # 현재 질문 제외
            ]
            result, error = ask_question(
                prompt, category, min_rating, use_reranker, use_hyde, chat_history
            )

            if error or result is None:
                response = f"""
⚠️ **오류가 발생했습니다**: {error or "알 수 없는 오류"}

**데이터 로드 방법:**
```bash
python scripts/load_all_categories.py
```
"""
                st.markdown(response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "sources": []
                })
            else:
                answer = result["answer"]
                source_docs = result.get("source_documents", [])

                st.markdown(answer)

                sources = extract_sources(source_docs)
                render_sources(sources)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

col1, col2 = st.columns([6, 1])
with col2:
    if st.button("🗑️ 초기화"):
        st.session_state.messages = []
        st.rerun()
