"""상품 검색 및 선택 컴포넌트"""

import streamlit as st
from typing import Any, Dict, List, Optional, Tuple


def search_products(
    query: str,
    vectorstore: Any,
    k: int = 50,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    검색어로 상품을 검색하고 상품별로 그룹화하여 반환합니다.

    :param query: 검색어
    :param vectorstore: ReviewVectorStore 인스턴스
    :param k: 검색할 최대 리뷰 수
    :param category: 카테고리 필터 (선택)
    :return: 상품 정보 리스트
    """
    try:
        filter_dict = None
        if category and category != "전체":
            filter_dict = {"category": category}

        results = vectorstore.similarity_search(
            query=query,
            k=k,
            filter=filter_dict
        )

        # 상품별로 그룹화
        products: Dict[str, Dict[str, Any]] = {}
        for doc in results:
            pid = doc.metadata.get("product_id", "unknown")
            if pid == "unknown":
                continue

            pname = doc.metadata.get("product_name", "Unknown Product")

            if pid not in products:
                products[pid] = {
                    "product_id": pid,
                    "product_name": pname,
                    "category": doc.metadata.get("category", "Unknown"),
                    "brand": doc.metadata.get("brand", ""),
                    "review_count": 0,
                    "ratings": [],
                    "sample_review": doc.page_content[:100]
                }

            products[pid]["review_count"] += 1
            rating = doc.metadata.get("rating")
            if rating:
                products[pid]["ratings"].append(rating)

        # 평균 평점 계산 및 리스트 변환
        product_list = []
        for pid, info in products.items():
            if info["ratings"]:
                info["avg_rating"] = round(
                    sum(info["ratings"]) / len(info["ratings"]), 1
                )
            else:
                info["avg_rating"] = 0
            del info["ratings"]
            product_list.append(info)

        # 리뷰 수 기준 정렬
        product_list.sort(key=lambda x: x["review_count"], reverse=True)

        return product_list

    except Exception as e:
        st.error(f"상품 검색 오류: {e}")
        return []


def search_and_select_product(
    vectorstore: Any,
    key_prefix: str,
    label: str = "상품 검색",
    placeholder: str = "상품명 또는 키워드...",
    categories: Optional[List[str]] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    검색 기반 상품 선택 UI 컴포넌트.

    :param vectorstore: ReviewVectorStore 인스턴스
    :param key_prefix: Streamlit 위젯 키 접두사
    :param label: 검색창 라벨
    :param placeholder: 검색창 플레이스홀더
    :param categories: 카테고리 목록 (선택)
    :return: (선택된 상품 ID, 상품명) 또는 (None, None)
    """
    # 세션 상태 초기화
    search_results_key = f"{key_prefix}_search_results"
    selected_key = f"{key_prefix}_selected"

    if search_results_key not in st.session_state:
        st.session_state[search_results_key] = []
    if selected_key not in st.session_state:
        st.session_state[selected_key] = None

    # 검색 폼
    with st.form(key=f"{key_prefix}_search_form"):
        col1, col2 = st.columns([3, 1])

        with col1:
            search_query = st.text_input(
                label,
                placeholder=placeholder,
                key=f"{key_prefix}_query"
            )

        with col2:
            if categories:
                category = st.selectbox(
                    "카테고리",
                    ["전체"] + categories,
                    key=f"{key_prefix}_category"
                )
            else:
                category = "전체"

        search_submitted = st.form_submit_button("🔍 검색", type="secondary")

    # 검색 실행
    if search_submitted and search_query:
        with st.spinner("상품을 검색하고 있습니다..."):
            products = search_products(
                query=search_query,
                vectorstore=vectorstore,
                k=50,
                category=category if category != "전체" else None
            )
            st.session_state[search_results_key] = products
            st.session_state[selected_key] = None

            if products:
                st.success(f"{len(products)}개의 상품을 찾았습니다.")
            else:
                st.warning("검색 결과가 없습니다.")

    # 검색 결과 표시 및 선택
    products = st.session_state[search_results_key]

    if products:
        # 상품 선택 옵션 생성
        options = []
        for p in products[:20]:  # 최대 20개 표시
            name = p["product_name"][:40] if p["product_name"] else "Unknown"
            if len(p.get("product_name", "")) > 40:
                name += "..."
            option = f"{name} (⭐{p['avg_rating']} | {p['review_count']}개 리뷰)"
            options.append(option)

        selected_idx = st.selectbox(
            "상품 선택",
            range(len(options)),
            format_func=lambda x: options[x],
            key=f"{key_prefix}_select",
            index=None,
            placeholder="검색 결과에서 상품을 선택하세요..."
        )

        if selected_idx is not None:
            selected_product = products[selected_idx]
            st.session_state[selected_key] = selected_product

            # 선택된 상품 정보 표시
            with st.container():
                st.markdown(f"**선택된 상품:** {selected_product['product_name']}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption(f"ID: {selected_product['product_id']}")
                with col2:
                    st.caption(f"평점: ⭐{selected_product['avg_rating']}")
                with col3:
                    st.caption(f"리뷰: {selected_product['review_count']}개")

            return selected_product["product_id"], selected_product["product_name"]

    # 직접 입력 옵션
    with st.expander("💡 상품 ID 직접 입력", expanded=False):
        direct_id = st.text_input(
            "상품 ID",
            placeholder="ASIN 또는 상품 ID 직접 입력...",
            key=f"{key_prefix}_direct"
        )
        if direct_id:
            return direct_id, None

    return None, None
