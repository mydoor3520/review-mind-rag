"""
QA Chat 페이지 E2E 테스트

리뷰 QA 채팅 페이지의 UI 요소와 기본 기능을 검증합니다.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestQAChatPageLoad:
    """QA Chat 페이지 로드 테스트"""
    
    def test_페이지_접근_가능(self, page_with_server):
        """QA Chat 페이지에 접근할 수 있어야 한다"""
        page, base_url = page_with_server
        
        # QA Chat 페이지로 이동
        page.goto(f"{base_url}/QA_Chat")
        page.wait_for_load_state("networkidle")
        
        # 페이지 타이틀 확인
        expect(page).to_have_title("리뷰 QA - Review Mind RAG")
    
    def test_페이지_헤더_표시(self, page_with_server):
        """페이지 헤더가 표시되어야 한다"""
        page, base_url = page_with_server
        page.goto(f"{base_url}/QA_Chat")
        page.wait_for_load_state("networkidle")
        
        header = page.locator("text=리뷰 QA 채팅")
        expect(header).to_be_visible()
    
    def test_페이지_설명_표시(self, page_with_server):
        """페이지 설명이 표시되어야 한다"""
        page, base_url = page_with_server
        page.goto(f"{base_url}/QA_Chat")
        page.wait_for_load_state("networkidle")
        
        description = page.locator("text=리뷰에 대해 자연어로 질문하고")
        expect(description).to_be_visible()


@pytest.mark.e2e
class TestQAChatSidebar:
    """QA Chat 사이드바 테스트"""
    
    def test_필터_설정_섹션_표시(self, page_with_server):
        """사이드바에 필터 설정 섹션이 표시되어야 한다"""
        page, base_url = page_with_server
        page.goto(f"{base_url}/QA_Chat")
        page.wait_for_load_state("networkidle")
        
        filter_section = page.locator("text=필터 설정")
        expect(filter_section).to_be_visible()
    
    def test_카테고리_선택_존재(self, page_with_server):
        """카테고리 선택 드롭다운이 있어야 한다"""
        page, base_url = page_with_server
        page.goto(f"{base_url}/QA_Chat")
        page.wait_for_load_state("networkidle")
        
        category_label = page.locator("text=카테고리")
        expect(category_label).to_be_visible()
    
    def test_최소_평점_슬라이더_존재(self, page_with_server):
        """최소 평점 슬라이더가 있어야 한다"""
        page, base_url = page_with_server
        page.goto(f"{base_url}/QA_Chat")
        page.wait_for_load_state("networkidle")
        
        rating_label = page.locator("text=최소 평점")
        expect(rating_label).to_be_visible()
    
    def test_예시_질문_섹션_표시(self, page_with_server):
        """예시 질문 섹션이 표시되어야 한다"""
        page, base_url = page_with_server
        page.goto(f"{base_url}/QA_Chat")
        page.wait_for_load_state("networkidle")
        
        example_section = page.locator("text=예시 질문")
        expect(example_section).to_be_visible()


@pytest.mark.e2e
class TestQAChatInput:
    """QA Chat 입력 테스트"""
    
    def test_채팅_입력_필드_존재(self, page_with_server):
        """채팅 입력 필드가 있어야 한다"""
        page, base_url = page_with_server
        page.goto(f"{base_url}/QA_Chat")
        page.wait_for_load_state("networkidle")
        
        # Streamlit chat_input은 textarea로 렌더링됨
        chat_input = page.locator("textarea[placeholder*='질문']")
        expect(chat_input).to_be_visible()
    
    def test_대화_초기화_버튼_존재(self, page_with_server):
        """대화 초기화 버튼이 있어야 한다"""
        page, base_url = page_with_server
        page.goto(f"{base_url}/QA_Chat")
        page.wait_for_load_state("networkidle")
        
        clear_button = page.locator("button:has-text('대화 초기화')")
        expect(clear_button).to_be_visible()


@pytest.mark.e2e
class TestQAChatInteraction:
    """QA Chat 상호작용 테스트"""
    
    def test_메시지_입력_후_표시(self, page_with_server):
        """메시지 입력 시 채팅 히스토리에 표시되어야 한다"""
        page, base_url = page_with_server
        page.goto(f"{base_url}/QA_Chat")
        page.wait_for_load_state("networkidle")
        
        # 채팅 입력
        chat_input = page.locator("textarea[placeholder*='질문']")
        test_message = "테스트 질문입니다"
        chat_input.fill(test_message)
        chat_input.press("Enter")
        
        # 메시지가 표시되는지 확인 (약간의 대기 필요)
        page.wait_for_timeout(2000)
        
        # 사용자 메시지 확인
        user_message = page.locator(f"text={test_message}")
        expect(user_message).to_be_visible()
    
    def test_AI_응답_표시(self, page_with_server):
        """질문 후 AI 응답이 표시되어야 한다"""
        page, base_url = page_with_server
        page.goto(f"{base_url}/QA_Chat")
        page.wait_for_load_state("networkidle")
        
        # 채팅 입력
        chat_input = page.locator("textarea[placeholder*='질문']")
        chat_input.fill("이 제품 어때요?")
        chat_input.press("Enter")
        
        # AI 응답 대기 (데모 응답 확인)
        page.wait_for_timeout(3000)
        
        # 응답에 포함될 텍스트 확인 (데모 응답의 일부)
        response = page.locator("text=Vector DB")
        expect(response).to_be_visible()
    
    def test_대화_초기화_동작(self, page_with_server):
        """대화 초기화 버튼 클릭 시 대화가 초기화되어야 한다"""
        page, base_url = page_with_server
        page.goto(f"{base_url}/QA_Chat")
        page.wait_for_load_state("networkidle")
        
        # 먼저 메시지 입력
        chat_input = page.locator("textarea[placeholder*='질문']")
        chat_input.fill("테스트 메시지")
        chat_input.press("Enter")
        page.wait_for_timeout(2000)
        
        # 초기화 버튼 클릭
        clear_button = page.locator("button:has-text('대화 초기화')")
        clear_button.click()
        
        # 페이지 리로드 대기
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        # 대화가 초기화되었는지 확인 (테스트 메시지가 없어야 함)
        # 초기화 후에는 chat_message 요소가 없어야 함
        chat_messages = page.locator("[data-testid='stChatMessage']")
        expect(chat_messages).to_have_count(0)
