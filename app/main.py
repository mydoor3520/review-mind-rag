"""
review-mind-rag Streamlit 메인 앱

RAG 기반 이커머스 리뷰 분석 대시보드
"""

import streamlit as st
from pathlib import Path
import sys

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 페이지 설정
st.set_page_config(
    page_title="Review Mind RAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
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
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# 메인 헤더
st.markdown('<p class="main-header">🧠 Review Mind RAG</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">RAG 기반 이커머스 리뷰 분석 시스템</p>', unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=ReviewMind", width=150)
    st.markdown("---")
    st.markdown("### 📊 시스템 상태")
    
    # 시스템 상태 표시 (추후 실제 데이터로 대체)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("리뷰 수", "0", help="Vector DB에 저장된 리뷰 수")
    with col2:
        st.metric("카테고리", "4", help="지원 카테고리 수")
    
    st.markdown("---")
    st.markdown("### ⚙️ 설정")
    
    # OpenAI API 키 입력
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="OpenAI API 키를 입력하세요"
    )
    
    if api_key:
        st.session_state["openai_api_key"] = api_key
        st.success("API 키가 설정되었습니다!")
    
    st.markdown("---")
    st.markdown("### 📚 페이지 안내")
    st.markdown("""
    - 🔍 **Search**: 상품 검색
    - 💬 **QA Chat**: 리뷰 질문
    - 📊 **Summary**: 리뷰 요약
    - ⚖️ **Compare**: 상품 비교
    """)

# 메인 콘텐츠
st.markdown("---")

# 기능 카드들
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

# 하단 정보
st.markdown("---")
st.markdown("### 🚀 시작하기")

with st.expander("사용 방법", expanded=True):
    st.markdown("""
    1. **API 키 설정**: 사이드바에서 OpenAI API 키를 입력하세요.
    2. **데이터 로드**: 데이터가 아직 없다면 먼저 리뷰 데이터를 로드해야 합니다.
    3. **기능 사용**: 원하는 기능을 선택하여 리뷰를 분석하세요.
    
    ```bash
    # 데이터 로드 예시 (터미널에서 실행)
    python -m src.data.loader --category Electronics --limit 1000
    ```
    """)

with st.expander("지원 카테고리"):
    st.markdown("""
    | 카테고리 | 설명 |
    |----------|------|
    | Electronics | 전자제품 (이어폰, 스피커, 케이블 등) |
    | Appliances | 가전제품 (에어프라이어, 청소기 등) |
    | Beauty | 뷰티/화장품 |
    | Home & Kitchen | 가구/주방용품 |
    """)

# 푸터
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #888;">Review Mind RAG v0.1.0 | '
    'Built with LangChain + Chroma + Streamlit</p>',
    unsafe_allow_html=True
)
