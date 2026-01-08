"""
상품 비교 페이지
"""

import streamlit as st

st.set_page_config(page_title="상품 비교 - Review Mind RAG", page_icon="⚖️", layout="wide")

st.title("⚖️ 상품 비교")
st.markdown("두 상품의 리뷰를 비교 분석합니다.")

# 상품 선택
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 상품 1")
    product_1 = st.text_input("상품 1 ID", placeholder="ASIN 또는 상품 ID...", key="p1")

with col2:
    st.markdown("### 상품 2")
    product_2 = st.text_input("상품 2 ID", placeholder="ASIN 또는 상품 ID...", key="p2")

if st.button("⚖️ 비교 분석", type="primary"):
    if product_1 and product_2:
        with st.spinner("리뷰를 비교 분석하고 있습니다..."):
            st.info("아직 데이터가 로드되지 않았습니다.")
            
            # 데모용 비교 표시
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"### 📦 상품 1: {product_1}")
                st.markdown("- 평균 평점: -")
                st.markdown("- 리뷰 수: -")
                
            with col2:
                st.markdown(f"### 📦 상품 2: {product_2}")
                st.markdown("- 평균 평점: -")
                st.markdown("- 리뷰 수: -")
    else:
        st.warning("두 상품의 ID를 모두 입력해주세요.")

st.markdown("---")
st.markdown("### 📋 비교 결과")
st.markdown("*비교 분석 결과가 여기에 표시됩니다.*")
