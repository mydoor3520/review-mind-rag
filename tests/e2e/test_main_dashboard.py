"""
메인 대시보드 E2E 테스트

Streamlit 메인 페이지의 UI 요소와 기본 기능을 검증합니다.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestMainDashboardLoad:
    """메인 대시보드 로드 테스트"""
    
    def test_페이지_타이틀_표시(self, page_with_server):
        """메인 페이지에 타이틀이 표시되어야 한다"""
        page, _ = page_with_server
        
        # 페이지 타이틀 확인
        expect(page).to_have_title("Review Mind RAG")
    
    def test_메인_헤더_표시(self, page_with_server):
        """메인 헤더 'Review Mind RAG'가 표시되어야 한다"""
        page, _ = page_with_server
        
        # 메인 헤더 텍스트 확인
        header = page.locator("text=Review Mind RAG").first
        expect(header).to_be_visible()
    
    def test_서브_헤더_표시(self, page_with_server):
        """서브 헤더 'RAG 기반 이커머스 리뷰 분석 시스템'이 표시되어야 한다"""
        page, _ = page_with_server
        
        sub_header = page.locator("text=RAG 기반 이커머스 리뷰 분석 시스템")
        expect(sub_header).to_be_visible()


@pytest.mark.e2e
class TestMainDashboardSidebar:
    """사이드바 테스트"""
    
    def test_사이드바_시스템_상태_표시(self, page_with_server):
        """사이드바에 시스템 상태 섹션이 표시되어야 한다"""
        page, _ = page_with_server
        
        # 시스템 상태 텍스트 확인
        system_status = page.locator("text=시스템 상태")
        expect(system_status).to_be_visible()
    
    def test_사이드바_API키_입력필드_존재(self, page_with_server):
        """사이드바에 OpenAI API Key 입력 필드가 있어야 한다"""
        page, _ = page_with_server
        
        # password 타입 입력 필드 확인 (API 키)
        api_input = page.locator("input[type='password']")
        expect(api_input).to_be_visible()
    
    def test_사이드바_페이지_안내_표시(self, page_with_server):
        """사이드바에 페이지 안내가 표시되어야 한다"""
        page, _ = page_with_server
        
        # 페이지 안내 섹션 확인
        page_guide = page.locator("text=페이지 안내")
        expect(page_guide).to_be_visible()


@pytest.mark.e2e
class TestMainDashboardFeatureCards:
    """기능 카드 테스트"""
    
    def test_검색_기능_카드_표시(self, page_with_server):
        """상품 검색 기능 카드가 표시되어야 한다"""
        page, _ = page_with_server
        
        search_card = page.locator("text=상품 검색")
        expect(search_card).to_be_visible()
    
    def test_QA_기능_카드_표시(self, page_with_server):
        """리뷰 QA 기능 카드가 표시되어야 한다"""
        page, _ = page_with_server
        
        qa_card = page.locator("text=리뷰 QA")
        expect(qa_card).to_be_visible()
    
    def test_요약_기능_카드_표시(self, page_with_server):
        """리뷰 요약 기능 카드가 표시되어야 한다"""
        page, _ = page_with_server
        
        summary_card = page.locator("text=리뷰 요약")
        expect(summary_card).to_be_visible()
    
    def test_비교_기능_카드_표시(self, page_with_server):
        """상품 비교 기능 카드가 표시되어야 한다"""
        page, _ = page_with_server
        
        compare_card = page.locator("text=상품 비교")
        expect(compare_card).to_be_visible()
    
    def test_검색_버튼_클릭_가능(self, page_with_server):
        """검색하기 버튼이 클릭 가능해야 한다"""
        page, _ = page_with_server
        
        search_button = page.locator("button:has-text('검색하기')")
        expect(search_button).to_be_visible()
        expect(search_button).to_be_enabled()
    
    def test_질문_버튼_클릭_가능(self, page_with_server):
        """질문하기 버튼이 클릭 가능해야 한다"""
        page, _ = page_with_server
        
        qa_button = page.locator("button:has-text('질문하기')")
        expect(qa_button).to_be_visible()
        expect(qa_button).to_be_enabled()


@pytest.mark.e2e
class TestMainDashboardExpanders:
    """하단 정보 영역 테스트"""
    
    def test_시작하기_섹션_표시(self, page_with_server):
        """시작하기 섹션이 표시되어야 한다"""
        page, _ = page_with_server
        
        getting_started = page.locator("text=시작하기")
        expect(getting_started).to_be_visible()
    
    def test_사용방법_expander_존재(self, page_with_server):
        """사용 방법 expander가 존재해야 한다"""
        page, _ = page_with_server
        
        usage_expander = page.locator("text=사용 방법")
        expect(usage_expander).to_be_visible()
    
    def test_지원카테고리_expander_존재(self, page_with_server):
        """지원 카테고리 expander가 존재해야 한다"""
        page, _ = page_with_server
        
        category_expander = page.locator("text=지원 카테고리")
        expect(category_expander).to_be_visible()


@pytest.mark.e2e
class TestMainDashboardFooter:
    """푸터 테스트"""
    
    def test_버전_정보_표시(self, page_with_server):
        """푸터에 버전 정보가 표시되어야 한다"""
        page, _ = page_with_server
        
        version_info = page.locator("text=v0.1.0")
        expect(version_info).to_be_visible()
    
    def test_기술스택_정보_표시(self, page_with_server):
        """푸터에 기술 스택 정보가 표시되어야 한다"""
        page, _ = page_with_server
        
        tech_stack = page.locator("text=LangChain + Chroma + Streamlit")
        expect(tech_stack).to_be_visible()
