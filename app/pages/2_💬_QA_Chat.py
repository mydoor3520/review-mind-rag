"""
리뷰 QA 채팅 페이지

RAG를 사용하여 리뷰 기반 질문-답변을 수행합니다.
"""

import streamlit as st
from pathlib import Path
import sys

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="리뷰 QA - Review Mind RAG",
    page_icon="💬",
    layout="wide"
)

st.title("💬 리뷰 QA 채팅")
st.markdown("리뷰에 대해 자연어로 질문하고 AI가 리뷰를 분석하여 답변합니다.")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None

# 사이드바 설정
with st.sidebar:
    st.markdown("### 필터 설정")
    
    category = st.selectbox(
        "카테고리",
        ["전체", "Electronics", "Appliances", "Beauty", "Home & Kitchen"],
        index=0
    )
    
    min_rating = st.slider(
        "최소 평점",
        min_value=1,
        max_value=5,
        value=1
    )
    
    st.markdown("---")
    st.markdown("### 예시 질문")
    st.markdown("""
    - "이 제품 소음이 어때?"
    - "배터리 수명은 어떤가요?"
    - "가격 대비 만족도는?"
    - "내구성에 대한 평가는?"
    """)

# 채팅 히스토리 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # 소스 문서 표시 (assistant 메시지인 경우)
        if message["role"] == "assistant" and "sources" in message:
            with st.expander("📚 참고한 리뷰", expanded=False):
                for i, source in enumerate(message["sources"][:3], 1):
                    st.markdown(f"""
                    **리뷰 {i}** (평점: {source.get('rating', 'N/A')}점)
                    > {source.get('text', '')[:200]}...
                    """)

# 채팅 입력
if prompt := st.chat_input("리뷰에 대해 질문하세요..."):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # AI 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("리뷰를 분석하고 있습니다..."):
            # TODO: 실제 RAG 체인 호출로 대체
            # 현재는 데모용 응답
            demo_response = f"""
죄송합니다. 현재 Vector DB에 리뷰 데이터가 로드되지 않았습니다.

**데이터를 먼저 로드해주세요:**
```bash
# 프로젝트 루트에서 실행
python -c "
from src.data.loader import AmazonReviewLoader
from src.data.preprocessor import ReviewPreprocessor
from src.rag.vectorstore import ReviewVectorStore

# 데이터 로드
loader = AmazonReviewLoader()
reviews = loader.load_category('Electronics', limit=1000)

# 전처리
preprocessor = ReviewPreprocessor()
documents = list(preprocessor.process_reviews(reviews))

# Vector DB 저장
vectorstore = ReviewVectorStore.from_documents(documents)
print(f'Loaded {{len(documents)}} reviews')
"
```

질문하신 내용: **{prompt}**
"""
            st.markdown(demo_response)
            
            # 메시지 저장
            st.session_state.messages.append({
                "role": "assistant",
                "content": demo_response,
                "sources": []
            })

# 채팅 초기화 버튼
if st.button("🗑️ 대화 초기화"):
    st.session_state.messages = []
    st.rerun()
