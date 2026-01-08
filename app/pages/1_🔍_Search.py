"""
상품 검색 페이지
"""

import streamlit as st

st.set_page_config(page_title="상품 검색 - Review Mind RAG", page_icon="🔍", layout="wide")

st.title("🔍 상품 검색")
st.markdown("카테고리별로 상품을 검색하고 리뷰를 확인하세요.")

# 검색 UI
col1, col2 = st.columns([3, 1])

with col1:
    search_query = st.text_input("검색어 입력", placeholder="상품명 또는 키워드...")

with col2:
    category = st.selectbox(
        "카테고리",
        ["전체", "Electronics", "Appliances", "Beauty", "Home & Kitchen"]
    )

if st.button("🔍 검색", type="primary"):
    if search_query:
        with st.spinner("검색 중..."):
            st.info("아직 데이터가 로드되지 않았습니다. 먼저 리뷰 데이터를 로드해주세요.")
    else:
        st.warning("검색어를 입력해주세요.")

st.markdown("---")
st.markdown("### 검색 결과")
st.markdown("*검색 결과가 여기에 표시됩니다.*")
