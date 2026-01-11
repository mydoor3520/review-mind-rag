"""
localhost:8510 실행 중인 서비스 E2E 테스트

Playwright를 사용하여 라이브 서비스를 테스트합니다.
"""

import pytest
from playwright.sync_api import sync_playwright, Page, expect


BASE_URL = "http://localhost:8501"


@pytest.fixture(scope="module")
def browser():
    """브라우저 인스턴스 생성"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    """새 페이지 생성"""
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        locale="ko-KR",
    )
    page = context.new_page()
    yield page
    page.close()
    context.close()


class TestMainDashboard:
    """메인 대시보드 테스트"""

    def test_페이지_로드(self, page: Page):
        """메인 페이지가 정상적으로 로드되어야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # 페이지 타이틀 확인
        expect(page).to_have_title("Review Mind RAG")

    def test_메인_헤더_표시(self, page: Page):
        """메인 헤더가 표시되어야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        header = page.locator("text=Review Mind RAG").first
        expect(header).to_be_visible()

    def test_서브헤더_표시(self, page: Page):
        """서브 헤더가 표시되어야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        sub_header = page.locator("text=RAG 기반 이커머스 리뷰 분석 시스템")
        expect(sub_header).to_be_visible()


class TestSidebar:
    """사이드바 테스트"""

    def test_시스템_상태_섹션(self, page: Page):
        """시스템 상태 섹션이 표시되어야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        system_status = page.locator("text=시스템 상태")
        expect(system_status).to_be_visible()

    def test_메뉴_섹션(self, page: Page):
        """메뉴 섹션이 표시되어야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        menu = page.locator("text=메뉴")
        expect(menu).to_be_visible()

    def test_서비스_상태_표시(self, page: Page):
        """서비스 상태가 표시되어야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # 서비스 정상 또는 점검 중 메시지 중 하나가 표시되어야 함
        service_ok = page.locator("text=서비스 정상")
        service_down = page.locator("text=서비스 점검 중")
        expect(service_ok.or_(service_down)).to_be_visible()


class TestFeatureCards:
    """기능 카드 테스트"""

    def test_상품검색_카드(self, page: Page):
        """상품 검색 카드가 표시되어야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        search_card = page.get_by_role("heading", name="상품 검색")
        expect(search_card).to_be_visible()

    def test_리뷰QA_카드(self, page: Page):
        """리뷰 QA 카드가 표시되어야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        qa_card = page.locator("text=리뷰 QA")
        expect(qa_card).to_be_visible()

    def test_리뷰요약_카드(self, page: Page):
        """리뷰 요약 카드가 표시되어야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        summary_card = page.get_by_role("heading", name="리뷰 요약")
        expect(summary_card).to_be_visible()

    def test_상품비교_카드(self, page: Page):
        """상품 비교 카드가 표시되어야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        compare_card = page.get_by_role("heading", name="상품 비교")
        expect(compare_card).to_be_visible()

    def test_검색버튼_클릭(self, page: Page):
        """검색하기 버튼이 클릭 가능해야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        search_button = page.locator("button:has-text('검색하기')")
        expect(search_button).to_be_visible()
        expect(search_button).to_be_enabled()

    def test_질문버튼_클릭(self, page: Page):
        """질문하기 버튼이 클릭 가능해야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        qa_button = page.locator("button:has-text('질문하기')")
        expect(qa_button).to_be_visible()
        expect(qa_button).to_be_enabled()


class TestInfoSections:
    """정보 섹션 테스트"""

    def test_지원카테고리_expander(self, page: Page):
        """지원 카테고리 expander가 존재해야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        category = page.locator("text=지원 카테고리")
        expect(category).to_be_visible()


class TestFooter:
    """푸터 테스트"""

    def test_푸터_정보(self, page: Page):
        """푸터에 프로젝트 정보가 표시되어야 한다"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        footer = page.locator("text=Review Mind RAG | Powered by LangChain + ChromaDB")
        expect(footer).to_be_visible()


class TestNavigation:
    """페이지 네비게이션 테스트"""

    def test_검색페이지_이동(self, page: Page):
        """검색 버튼 클릭 시 Search 페이지로 이동"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        search_button = page.locator("button:has-text('검색하기')")
        search_button.click()

        page.wait_for_timeout(2000)
        expect(page).to_have_url(f"{BASE_URL}/Search")

    def test_QA페이지_이동(self, page: Page):
        """질문 버튼 클릭 시 QA 페이지로 이동"""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        qa_button = page.locator("button:has-text('질문하기')")
        qa_button.click()

        page.wait_for_timeout(2000)
        expect(page).to_have_url(f"{BASE_URL}/QA_Chat")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
