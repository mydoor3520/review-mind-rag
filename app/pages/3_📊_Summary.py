"""
리뷰 요약 페이지
"""

import streamlit as st

st.set_page_config(page_title="리뷰 요약 - Review Mind RAG", page_icon="📊", layout="wide")

st.title("📊 리뷰 요약")
st.markdown("상품별 리뷰를 자동으로 요약하고 감성을 분석합니다.")

# 상품 선택
product_id = st.text_input("상품 ID 입력", placeholder="ASIN 또는 상품 ID...")

if st.button("📊 요약 생성", type="primary"):
    if product_id:
        with st.spinner("리뷰를 분석하고 있습니다..."):
            st.info("아직 데이터가 로드되지 않았습니다.")
            
            # 데모용 요약 표시
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✅ 장점")
                st.markdown("- 데이터 로드 후 표시됩니다")
                
            with col2:
                st.markdown("### ❌ 단점")
                st.markdown("- 데이터 로드 후 표시됩니다")
    else:
        st.warning("상품 ID를 입력해주세요.")

st.markdown("---")

# 감성 분석 차트 영역
st.markdown("### 감성 분석")
st.markdown("*리뷰의 긍정/부정/중립 비율이 여기에 표시됩니다.*")
